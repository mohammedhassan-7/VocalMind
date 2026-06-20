#!/usr/bin/env python3
"""Batch-ingest audio files from a host folder through the full interaction pipeline."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_EXTENSIONS = {".wav", ".mp3"}
REPO_ROOT = Path(__file__).resolve().parents[2]
_AUDIO_FILENAME_AGENT_PATTERN = re.compile(r"^CALL_\d{2}_(?P<agent>[a-zA-Z]+)_")


@dataclass
class FileResult:
    filename: str
    interaction_id: str = ""
    status: str = ""
    overall_score: str = ""
    llm_triggers_present: str = ""
    error_message: str = ""
    skipped_poll: bool = False


def _request(
    method: str,
    url: str,
    *,
    data: dict | None = None,
    form_body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 120.0,
) -> tuple[int, str]:
    body = form_body
    req_headers = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, method=method)
    for key, value in req_headers.items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def login(base: str, email: str, password: str) -> str:
    form = urllib.parse.urlencode({"username": email, "password": password}).encode("utf-8")
    status, text = _request(
        "POST",
        f"{base}/auth/login/access-token",
        form_body=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=90,
    )
    if status != 200:
        raise RuntimeError(f"login failed ({status}): {text}")
    return json.loads(text)["access_token"]


def list_agents(base: str, token: str) -> list[dict]:
    status, text = _request("GET", f"{base}/agents", headers={"Authorization": f"Bearer {token}"})
    if status != 200:
        raise RuntimeError(f"agents failed ({status}): {text}")
    return json.loads(text)


def get_default_agent_id(base: str, token: str) -> str:
    agents = list_agents(base, token)
    if not agents:
        raise RuntimeError("no agents found for organization")
    return agents[0]["id"]


def _extract_agent_token_from_filename(filename: str) -> str | None:
    match = _AUDIO_FILENAME_AGENT_PATTERN.match(Path(filename).name)
    if not match:
        return None
    return match.group("agent").lower()


def resolve_agent_id_for_file(
    agents: list[dict],
    *,
    rel_under_org: Path,
    filename: str,
    default_agent_id: str,
) -> str:
    """Map audio/<org>/<agent>/CALL_*.wav folder layout (or filename token) to agent user id."""
    by_name = {str(agent.get("name", "")).strip().lower(): agent["id"] for agent in agents}
    candidates: list[str] = []
    parts = rel_under_org.parts
    if len(parts) >= 2:
        candidates.append(parts[0].lower())
    token = _extract_agent_token_from_filename(filename)
    if token:
        candidates.append(token)
    for candidate in candidates:
        agent_id = by_name.get(candidate)
        if agent_id:
            return agent_id
    return default_agent_id


def discover_audio_files(folder: Path, org_slug: str) -> list[tuple[Path, Path]]:
    """Return (source_path, relative_dest_under_org) pairs."""
    folder = folder.resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"folder not found: {folder}")

    discovered: list[tuple[Path, Path]] = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        rel = path.relative_to(folder)
        parts = rel.parts
        if org_slug in parts:
            idx = parts.index(org_slug)
            rel_under_org = Path(*parts[idx + 1 :]) if idx + 1 < len(parts) else Path(path.name)
        else:
            rel_under_org = rel
        discovered.append((path, rel_under_org))
    return discovered


def container_path_for(org_slug: str, rel_under_org: Path) -> str:
    return f"/app/storage/audio/{org_slug}/{rel_under_org.as_posix()}"


def ensure_copied(source: Path, org_slug: str, rel_under_org: Path) -> tuple[Path, str]:
    """Copy into repo storage if needed; return host dest and container storage_path."""
    dest = REPO_ROOT / "storage" / "audio" / org_slug / rel_under_org
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copy2(source, dest)
    elif dest.stat().st_size != source.stat().st_size:
        shutil.copy2(source, dest)
    return dest, container_path_for(org_slug, rel_under_org)


def poll_until_done(
    base: str,
    token: str,
    interaction_id: str,
    *,
    poll_interval: float,
    timeout_seconds: float,
) -> tuple[str, str]:
    deadline = time.monotonic() + timeout_seconds
    last_status = ""
    last_error = ""
    while time.monotonic() < deadline:
        status_code, text = _request(
            "GET",
            f"{base}/interactions/{interaction_id}/processing-status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        if status_code != 200:
            last_error = f"poll HTTP {status_code}: {text}"
            time.sleep(poll_interval)
            continue
        payload = json.loads(text)
        last_status = payload.get("status") or ""
        if last_status in ("completed", "failed"):
            jobs = payload.get("jobs") or []
            for job in jobs:
                if job.get("status") == "failed" and job.get("errorMessage"):
                    last_error = str(job["errorMessage"])
            return last_status, last_error
        time.sleep(poll_interval)
    return "timeout", f"timed out after {int(timeout_seconds)}s"


def fetch_summary(
    base: str,
    token: str,
    interaction_id: str,
) -> tuple[str, str, str]:
    status_code, text = _request(
        "GET",
        f"{base}/interactions/{interaction_id}?include_llm_triggers=true",
        headers={"Authorization": f"Bearer {token}"},
        timeout=180,
    )
    if status_code != 200:
        return "", "no", f"detail HTTP {status_code}"
    detail = json.loads(text)
    inter = detail.get("interaction") or {}
    overall = inter.get("overallScore")
    overall_str = "" if overall is None else str(overall)
    llm = detail.get("llmTriggers")
    if isinstance(llm, dict) and llm.get("available") is not False:
        keys = ("emotionShift", "processAdherence", "nliPolicy")
        present = all(llm.get(k) is not None for k in keys)
        return overall_str, "yes" if present else "partial", ""
    return overall_str, "no", (llm or {}).get("error", "") if isinstance(llm, dict) else "missing"


def process_file_sync(
    *,
    source: Path,
    rel_under_org: Path,
    org_slug: str,
    base: str,
    token: str,
    agent_id: str,
    poll_interval: float,
    timeout_seconds: float,
    dry_run: bool,
) -> FileResult:
    label = rel_under_org.as_posix()
    result = FileResult(filename=label)
    try:
        _dest, container_path = ensure_copied(source, org_slug, rel_under_org)
        if dry_run:
            result.status = "dry-run"
            result.interaction_id = container_path
            return result

        create_payload = {
            "storage_path": container_path,
            "agent_id": agent_id,
            "verify_exists": False,
        }
        status_code, text = _request(
            "POST",
            f"{base}/interactions/from-storage",
            data=create_payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        if status_code != 200:
            raise RuntimeError(f"from-storage failed ({status_code}): {text}")

        created = json.loads(text)
        interaction_id = created["interactionId"]
        result.interaction_id = interaction_id

        if created.get("reused") and created.get("status") == "completed":
            result.status = "completed"
            result.skipped_poll = True
            overall, llm_present, err = fetch_summary(base, token, interaction_id)
            result.overall_score = overall
            result.llm_triggers_present = llm_present
            if err:
                result.error_message = err
            return result

        final_status, err = poll_until_done(
            base,
            token,
            interaction_id,
            poll_interval=poll_interval,
            timeout_seconds=timeout_seconds,
        )
        result.status = final_status
        if err:
            result.error_message = err
        if final_status == "completed":
            overall, llm_present, detail_err = fetch_summary(base, token, interaction_id)
            result.overall_score = overall
            result.llm_triggers_present = llm_present
            if detail_err and not result.error_message:
                result.error_message = detail_err
    except Exception as exc:
        result.status = "failed"
        result.error_message = str(exc)
    return result


async def process_file(
    sem: asyncio.Semaphore,
    *,
    source: Path,
    rel_under_org: Path,
    org_slug: str,
    base: str,
    token: str,
    agent_id: str,
    poll_interval: float,
    timeout_seconds: float,
    dry_run: bool,
) -> FileResult:
    async with sem:
        return await asyncio.to_thread(
            process_file_sync,
            source=source,
            rel_under_org=rel_under_org,
            org_slug=org_slug,
            base=base,
            token=token,
            agent_id=agent_id,
            poll_interval=poll_interval,
            timeout_seconds=timeout_seconds,
            dry_run=dry_run,
        )


def print_summary_table(results: list[FileResult]) -> None:
    headers = ("filename", "interaction_id", "status", "overall_score", "llm_triggers_present")
    rows = [
        (
            r.filename,
            r.interaction_id or "-",
            r.status or "-",
            r.overall_score or "-",
            r.llm_triggers_present or "-",
        )
        for r in results
    ]
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row)]
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(fmt.format(*row))
    for r in results:
        if r.error_message:
            print(f"  error [{r.filename}]: {r.error_message}")
        if r.skipped_poll:
            print(f"  note [{r.filename}]: reused completed interaction, poll skipped")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch ingest audio folder into VocalMind pipeline.")
    parser.add_argument("--folder", required=True, help="Host folder to scan recursively")
    parser.add_argument("--org", required=True, help="Organization slug (login user must belong to this org)")
    parser.add_argument("--email", default=os.environ.get("INGEST_EMAIL"))
    parser.add_argument("--password", default=os.environ.get("INGEST_PASSWORD"))
    parser.add_argument("--base", default="http://localhost:8000/api/v1")
    parser.add_argument("--poll-interval", type=float, default=15.0)
    parser.add_argument("--timeout", type=float, default=1800.0, help="Per-interaction poll timeout seconds")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


async def main_async() -> int:
    args = parse_args()
    if not args.dry_run and (not args.email or not args.password):
        print("email/password required (or set INGEST_EMAIL / INGEST_PASSWORD)", file=sys.stderr)
        return 1

    folder = Path(args.folder)
    files = discover_audio_files(folder, args.org)
    if not files:
        print(f"no .wav/.mp3 files under {folder}", file=sys.stderr)
        return 1

    base = args.base.rstrip("/")
    token = ""
    agents: list[dict] = []
    default_agent_id = ""
    if not args.dry_run:
        token = login(base, args.email, args.password)
        agents = list_agents(base, token)
        default_agent_id = get_default_agent_id(base, token)

    if args.dry_run:
        print(f"DRY RUN — {len(files)} file(s) for org={args.org}")
        for source, rel in files:
            parts = rel.parts
            folder_agent = parts[0] if len(parts) >= 2 else "-"
            file_agent = _extract_agent_token_from_filename(source.name) or "-"
            print(
                f"  {source} -> {container_path_for(args.org, rel)} "
                f"(folder_agent={folder_agent}, file_agent={file_agent})"
            )
        return 0

    sem = asyncio.Semaphore(max(1, args.concurrency))
    tasks = [
        process_file(
            sem,
            source=source,
            rel_under_org=rel,
            org_slug=args.org,
            base=base,
            token=token,
            agent_id=resolve_agent_id_for_file(
                agents,
                rel_under_org=rel,
                filename=source.name,
                default_agent_id=default_agent_id,
            ),
            poll_interval=args.poll_interval,
            timeout_seconds=args.timeout,
            dry_run=False,
        )
        for source, rel in files
    ]
    results = await asyncio.gather(*tasks)
    print_summary_table(results)
    failed = sum(1 for r in results if r.status not in ("completed",))
    return 1 if failed else 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
