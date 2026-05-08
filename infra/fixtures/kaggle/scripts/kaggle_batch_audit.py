"""Batch audit: test all 5 audio files against all 6 Kaggle endpoints."""
from __future__ import annotations
import asyncio, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import httpx

if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://etta-cleistogamous-untangentially.ngrok-free.dev"
HEADERS = {"ngrok-skip-browser-warning": "true"}
TIMEOUT = httpx.Timeout(600.0, connect=30.0)
REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"

AUDIO_FILES = [
    Path("G:/projects/VocalMind/AudioData/easy_no_overlap.wav"),
    Path("G:/projects/VocalMind/AudioData/easy_overlap.wav"),
    Path("G:/projects/VocalMind/AudioData/hard_overlap.wav"),
    Path("G:/projects/VocalMind/AudioData/medium_overlap.wav"),
    Path("G:/projects/VocalMind/AudioData/telecom_call.wav"),
]

ENDPOINTS = [
    ("GET", "/health", None),
    ("POST", "/vad", True),
    ("POST", "/diarize", True),
    ("POST", "/transcribe", True),
    ("POST", "/emotion", True),
    ("POST", "/full", True),
]


async def test_endpoint(client, method, endpoint, audio_bytes=None, filename=None):
    url = f"{BASE}{endpoint}"
    t0 = time.monotonic()
    try:
        if method == "GET":
            r = await client.get(url, headers=HEADERS)
        else:
            r = await client.post(url, files={"file": (filename, audio_bytes, "audio/wav")}, headers=HEADERS)
        elapsed = round(time.monotonic() - t0, 3)
        try:
            body = r.json()
        except Exception:
            body = r.text[:300]
        return {"status": r.status_code, "elapsed_s": elapsed, "body": body}
    except httpx.TimeoutException as e:
        return {"status": None, "elapsed_s": round(time.monotonic() - t0, 3), "error": f"Timeout: {e}"}
    except httpx.RequestError as e:
        return {"status": None, "elapsed_s": round(time.monotonic() - t0, 3), "error": f"RequestError: {e}"}
    except Exception as e:
        return {"status": None, "elapsed_s": round(time.monotonic() - t0, 3), "error": f"{type(e).__name__}: {e}"}


async def run_batch():
    report = {"started_utc": datetime.now(timezone.utc).isoformat(), "files": []}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for af in AUDIO_FILES:
            if not af.exists():
                print(f"SKIP {af.name} — not found")
                continue
            audio_bytes = af.read_bytes()
            size_mb = len(audio_bytes) / (1024 * 1024)
            file_report = {"filename": af.name, "size_mb": round(size_mb, 2), "endpoints": {}}
            print(f"\n{'='*60}")
            print(f"FILE: {af.name} ({size_mb:.1f} MB)")
            print(f"{'='*60}")

            for method, endpoint, needs_audio in ENDPOINTS:
                label = f"{method} {endpoint}"
                print(f"  {label:25s} ", end="", flush=True)
                ab = audio_bytes if needs_audio else None
                fn = af.name if needs_audio else None
                r = await test_endpoint(client, method, endpoint, ab, fn)
                file_report["endpoints"][endpoint] = r

                status = r.get("status", "ERR")
                elapsed = r.get("elapsed_s", 0)
                body = r.get("body")
                err = r.get("error")

                if status == 200 and isinstance(body, dict):
                    keys = list(body.keys())
                    seg_count = len(body.get("segments", body.get("speech_segments", [])))
                    detail = f"keys={keys}" if seg_count == 0 else f"keys={keys} segments={seg_count}"
                    if "text" in body:
                        detail += f" text={str(body['text'])[:60]}..."
                    if "top_emotion" in body:
                        detail += f" top={body['top_emotion']}"
                    print(f"200  {elapsed:6.1f}s  {detail}")
                elif status == 200:
                    print(f"200  {elapsed:6.1f}s  body={str(body)[:80]}")
                elif status:
                    body_hint = ""
                    if isinstance(body, str) and "ngrok" in body.lower():
                        body_hint = " [ngrok HTML]"
                    elif isinstance(body, str) and "Internal Server Error" in body:
                        body_hint = " [500 from server]"
                    print(f"{status}  {elapsed:6.1f}s{body_hint}")
                else:
                    print(f"ERR  {elapsed:6.1f}s  {err[:80] if err else ''}")

                # Small delay between requests to let GPU recover
                if needs_audio:
                    await asyncio.sleep(2)

            report["files"].append(file_report)

    report["completed_utc"] = datetime.now(timezone.utc).isoformat()

    # Save
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPORT_DIR / f"kaggle_batch_audit_{ts}.json"
    path.write_text(json.dumps(report, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport saved: {path}")

    # Summary table
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'File':<25s} {'health':>7s} {'vad':>7s} {'diarize':>7s} {'transcribe':>10s} {'emotion':>7s} {'full':>7s}")
    for fr in report["files"]:
        row = [fr["filename"][:24]]
        for ep in ["/health", "/vad", "/diarize", "/transcribe", "/emotion", "/full"]:
            r = fr["endpoints"].get(ep, {})
            s = r.get("status")
            if s == 200:
                row.append(f"{r['elapsed_s']:.0f}s")
            elif s:
                row.append(f"{s}")
            else:
                row.append("ERR")
        print(f"{row[0]:<25s} {row[1]:>7s} {row[2]:>7s} {row[3]:>7s} {row[4]:>10s} {row[5]:>7s} {row[6]:>7s}")

    return report


if __name__ == "__main__":
    asyncio.run(run_batch())