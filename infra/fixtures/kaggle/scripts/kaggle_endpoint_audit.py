"""Comprehensive Kaggle inference server endpoint audit.

Tests every remote endpoint with the exact audio file CALL_03_marcus_tech_support.wav,
captures complete raw JSON responses, and includes malformed-request error-handling
checks. Results are saved as a timestamped JSON report.

Usage:
    python infra/fixtures/kaggle/scripts/kaggle_endpoint_audit.py
    python infra/fixtures/kaggle/scripts/kaggle_endpoint_audit.py --base-url <URL> --audio-file <path>
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

DEFAULT_BASE_URL = "https://etta-cleistogamous-untangentially.ngrok-free.dev"
DEFAULT_AUDIO_FILE = Path("../../AudioData/CALL_03_marcus_tech_support.wav")
HEADERS = {"ngrok-skip-browser-warning": "true"}
REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _test_health(client: httpx.AsyncClient, base_url: str) -> dict:
    result = {
        "endpoint": "GET /health",
        "method": "GET",
        "url": f"{base_url}/health",
        "request_summary": {"method": "GET", "endpoint": "/health"},
        "timestamp_utc": _utcnow_iso(),
        "status_code": None,
        "response_body": None,
        "error": None,
        "elapsed_s": None,
    }
    try:
        import time

        t0 = time.monotonic()
        resp = await client.get(f"{base_url}/health", headers=HEADERS)
        result["elapsed_s"] = round(time.monotonic() - t0, 3)
        result["status_code"] = resp.status_code
        try:
            result["response_body"] = resp.json()
        except Exception:
            result["response_body"] = resp.text[:2000]
    except Exception as exc:
        result["error"] = f"{exc.__class__.__name__}: {exc}"
    return result


async def _test_post_endpoint(
    client: httpx.AsyncClient,
    base_url: str,
    endpoint: str,
    audio_bytes: bytes,
    filename: str = "CALL_03_marcus_tech_support.wav",
    content_type: str = "audio/wav",
) -> dict:
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    result = {
        "endpoint": f"POST /{endpoint.lstrip('/')}",
        "method": "POST",
        "url": url,
        "request_summary": {
            "method": "POST",
            "endpoint": f"/{endpoint.lstrip('/')}",
            "payload": "multipart/form-data",
            "file_field_name": "file",
            "filename": filename,
            "content_type": content_type,
            "audio_bytes_size": len(audio_bytes),
        },
        "timestamp_utc": _utcnow_iso(),
        "status_code": None,
        "response_body": None,
        "error": None,
        "elapsed_s": None,
    }
    try:
        import time

        t0 = time.monotonic()
        resp = await client.post(
            url,
            files={"file": (filename, audio_bytes, content_type)},
            headers=HEADERS,
        )
        result["elapsed_s"] = round(time.monotonic() - t0, 3)
        result["status_code"] = resp.status_code
        try:
            result["response_body"] = resp.json()
        except Exception:
            result["response_body"] = resp.text[:4000]
    except httpx.TimeoutException as exc:
        result["error"] = f"Timeout: {exc}"
    except httpx.RequestError as exc:
        result["error"] = f"RequestError: {exc}"
    except Exception as exc:
        result["error"] = f"{exc.__class__.__name__}: {exc}"
    return result


async def _test_malformed_request(
    client: httpx.AsyncClient,
    base_url: str,
    endpoint: str,
    test_name: str,
    *,
    send_empty: bool = False,
    send_bad_content_type: bool = False,
    send_no_file: bool = False,
    send_non_audio: bool = False,
) -> dict:
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    summary = {
        "method": "POST",
        "endpoint": f"/{endpoint.lstrip('/')}",
        "test_type": test_name,
    }
    if send_empty:
        summary["payload"] = "empty file field (0 bytes)"
    elif send_bad_content_type:
        summary["payload"] = "file with wrong content_type (application/json)"
    elif send_no_file:
        summary["payload"] = "no file field at all"
    elif send_non_audio:
        summary["payload"] = "non-audio file (text/plain .txt)"

    result = {
        "endpoint": f"POST /{endpoint.lstrip('/')} — {test_name}",
        "method": "POST",
        "url": url,
        "request_summary": summary,
        "timestamp_utc": _utcnow_iso(),
        "status_code": None,
        "response_body": None,
        "error": None,
        "elapsed_s": None,
    }
    try:
        import time

        t0 = time.monotonic()
        if send_empty:
            resp = await client.post(
                url,
                files={"file": ("empty.wav", b"", "audio/wav")},
                headers=HEADERS,
            )
        elif send_bad_content_type:
            resp = await client.post(
                url,
                files={"file": ("audio.wav", b"not audio data", "application/json")},
                headers=HEADERS,
            )
        elif send_no_file:
            resp = await client.post(url, data={}, headers=HEADERS)
        elif send_non_audio:
            resp = await client.post(
                url,
                files={"file": ("test.txt", b"this is not audio", "text/plain")},
                headers=HEADERS,
            )
        else:
            resp = await client.post(url, headers=HEADERS)
        result["elapsed_s"] = round(time.monotonic() - t0, 3)
        result["status_code"] = resp.status_code
        try:
            result["response_body"] = resp.json()
        except Exception:
            result["response_body"] = resp.text[:2000]
    except Exception as exc:
        result["error"] = f"{exc.__class__.__name__}: {exc}"
    return result


async def run_audit(base_url: str, audio_file: Path, timeout_s: int) -> dict:
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    audio_bytes = audio_file.read_bytes()
    base = base_url.rstrip("/")

    report = {
        "audit_meta": {
            "script": "kaggle_endpoint_audit.py",
            "base_url": base_url,
            "audio_file": str(audio_file.resolve()),
            "audio_file_size_bytes": len(audio_bytes),
            "timeout_seconds": timeout_s,
            "started_utc": _utcnow_iso(),
        },
        "results": [],
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(float(timeout_s), connect=30.0)) as client:
        # 1. Health check
        print("=" * 60)
        print("1/6  GET /health")
        r = await _test_health(client, base)
        report["results"].append(r)
        _print_result(r)

        if r["status_code"] != 200:
            print("WARNING: /health returned non-200. Server may be down.")
            print("Continuing with remaining tests anyway...\n")

        # 2. VAD
        print("=" * 60)
        print("2/6  POST /vad")
        r = await _test_post_endpoint(client, base, "vad", audio_bytes)
        report["results"].append(r)
        _print_result(r)

        # 3. Diarize
        print("=" * 60)
        print("3/6  POST /diarize")
        r = await _test_post_endpoint(client, base, "diarize", audio_bytes)
        report["results"].append(r)
        _print_result(r)

        # 4. Transcribe
        print("=" * 60)
        print("4/6  POST /transcribe")
        r = await _test_post_endpoint(client, base, "transcribe", audio_bytes)
        report["results"].append(r)
        _print_result(r)

        # 5. Emotion
        print("=" * 60)
        print("5/6  POST /emotion")
        r = await _test_post_endpoint(client, base, "emotion", audio_bytes)
        report["results"].append(r)
        _print_result(r)

        # 6. Full (combined)
        print("=" * 60)
        print("6/6  POST /full")
        r = await _test_post_endpoint(client, base, "full", audio_bytes)
        report["results"].append(r)
        _print_result(r)

        # ── Error-handling tests ──────────────────────────────────────
        print("\n" + "=" * 60)
        print("ERROR-HANDLING TESTS")
        print("=" * 60)

        # Empty file on /emotion
        print("\n7  POST /emotion — empty file")
        r = await _test_malformed_request(client, base, "emotion", "empty_file", send_empty=True)
        report["results"].append(r)
        _print_result(r)

        # Non-audio file on /transcribe
        print("\n8  POST /transcribe — non-audio file (.txt)")
        r = await _test_malformed_request(client, base, "transcribe", "non_audio_file", send_non_audio=True)
        report["results"].append(r)
        _print_result(r)

        # No file field on /full
        print("\n9  POST /full — missing file field")
        r = await _test_malformed_request(client, base, "full", "no_file_field", send_no_file=True)
        report["results"].append(r)
        _print_result(r)

        # Bad content-type on /vad
        print("\n10 POST /vad — wrong content-type")
        r = await _test_malformed_request(client, base, "vad", "bad_content_type", send_bad_content_type=True)
        report["results"].append(r)
        _print_result(r)

    report["audit_meta"]["completed_utc"] = _utcnow_iso()

    success_count = sum(
        1 for r in report["results"][:6] if r["status_code"] == 200
    )
    report["audit_meta"]["valid_requests_succeeded"] = success_count
    report["audit_meta"]["valid_requests_total"] = 6

    error_test_count = len(report["results"]) - 6
    error_rejected = sum(
        1 for r in report["results"][6:] if r["status_code"] and r["status_code"] >= 400
    )
    report["audit_meta"]["error_requests_rejected"] = error_rejected
    report["audit_meta"]["error_requests_total"] = error_test_count

    return report


def _print_result(r: dict) -> None:
    status = r.get("status_code")
    elapsed = r.get("elapsed_s")
    err = r.get("error")
    body = r.get("response_body")

    print(f"  Status: {status}  Elapsed: {elapsed}s")
    if err:
        print(f"  Error:  {err}")
    if body and status == 200:
        _print_body_summary(body)
    elif body:
        text = json.dumps(body, indent=2) if isinstance(body, (dict, list)) else str(body)
        print(f"  Body:   {text[:500]}")
    print()


def _print_body_summary(body) -> None:
    if isinstance(body, dict):
        keys = list(body.keys())
        print(f"  Keys:   {keys}")
        if "segments" in body:
            segs = body["segments"]
            print(f"  Segments: {len(segs)}")
            if segs and isinstance(segs[0], dict):
                print(f"  Segment[0] keys: {list(segs[0].keys())}")
        if "text" in body:
            t = body["text"]
            print(f"  Text: {t[:120]}..." if len(str(t)) > 120 else f"  Text: {t}")
        if "language" in body:
            print(f"  Language: {body['language']}")
        if "top_emotion" in body:
            print(f"  Top emotion: {body['top_emotion']}")
        if "emotions" in body:
            print(f"  Emotions: {body['emotions'][:5]}")
        if "speech_segments" in body or "total_segments" in body:
            if "speech_segments" in body:
                print(f"  Speech segments: {len(body['speech_segments'])}")
            if "total_segments" in body:
                print(f"  Total segments: {body['total_segments']}")
    elif isinstance(body, list):
        print(f"  List length: {len(body)}")


def save_report(report: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPORT_DIR / f"kaggle_audit_{ts}.json"
    path.write_text(json.dumps(report, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Comprehensive Kaggle inference server endpoint audit.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Kaggle/ngrok base URL.")
    audio_default = Path(__file__).resolve().parents[3] / "AudioData" / "CALL_03_marcus_tech_support.wav"
    parser.add_argument(
        "--audio-file",
        type=Path,
        default=audio_default,
        help="Path to audio file for testing.",
    )
    parser.add_argument("--timeout", type=int, default=600, help="Request timeout in seconds.")
    args = parser.parse_args()

    print("VocalMind Kaggle Inference Server — Endpoint Audit")
    print(f"Base URL:  {args.base_url}")
    print(f"Audio:     {args.audio_file} ({args.audio_file.stat().st_size / (1024*1024):.1f} MB)")
    print(f"Timeout:   {args.timeout}s")
    print()

    report = asyncio.run(run_audit(args.base_url, args.audio_file, args.timeout))

    path = save_report(report)
    print("\n" + "=" * 60)
    print(f"Report saved: {path}")

    meta = report["audit_meta"]
    print(f"Valid requests:  {meta['valid_requests_succeeded']}/{meta['valid_requests_total']} succeeded")
    print(f"Error requests:  {meta['error_requests_rejected']}/{meta['error_requests_total']} properly rejected")

    if meta["valid_requests_succeeded"] == meta["valid_requests_total"]:
        print("ALL VALID REQUESTS PASSED")
    else:
        print("SOME VALID REQUESTS FAILED — see report for details")

    if meta["error_requests_rejected"] == meta["error_requests_total"]:
        print("ALL ERROR-HANDLING TESTS PASSED")
    else:
        print("SOME ERROR-HANDLING TESTS PASSED — see report for details")


if __name__ == "__main__":
    main()