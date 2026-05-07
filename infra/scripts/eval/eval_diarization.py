"""Evaluate pure diarization DER against the VoxConverse benchmark.

Downloads VoxConverse test audio + RTTM ground truth, sends each clip to the
WhisperX /transcribe endpoint, and computes Diarization Error Rate (DER) with
its components (missed detection, false alarm, speaker confusion) using
pyannote.metrics.  Produces a structured JSON report compatible with the
infra/benchmarks eval framework.

Usage:
    python eval_diarization.py --server-url http://localhost:8003 --subset-size 10
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import requests
import soundfile as sf
from pyannote.core import Annotation, Segment, Timeline
from pyannote.metrics.diarization import DiarizationErrorRate

from eval_common import REPORTS_DIR, ROOT, THRESHOLDS_PATH, load_json, write_json

VOXCONVERSE_AUDIO_URL = "https://www.robots.ox.ac.uk/~vgg/data/voxconverse/data/voxconverse_test_wav.zip"
VOXCONVERSE_RTTM_URL = "https://github.com/joonson/voxconverse/archive/refs/heads/master.zip"
SERVER_URL = "http://localhost:8003"
ENDPOINT = "/transcribe"
SUBSET_SIZE = 100
MAX_DURATION = 240.0
REQUEST_TIMEOUT = 300
DEFAULT_DATA_DIR = ROOT / "storage" / "eval_data"
RTTM_SUBDIR = Path("voxconverse-master") / "test"


def _ensure_dataset(data_dir: Path) -> tuple[Path, Path]:
    audio_root = data_dir / "vox_audio"
    rttm_root = data_dir / "vox_rttm"

    if (audio_root / "voxconverse_test_wav").is_dir() and (rttm_root / RTTM_SUBDIR).is_dir():
        return audio_root, rttm_root

    if not (audio_root / "voxconverse_test_wav").is_dir():
        _download_extract(VOXCONVERSE_AUDIO_URL, data_dir / "audio.zip", audio_root)

    if not (rttm_root / RTTM_SUBDIR).is_dir():
        _download_extract(VOXCONVERSE_RTTM_URL, data_dir / "rttm.zip", rttm_root)

    return audio_root, rttm_root


def _download_extract(url: str, zip_path: Path, extract_to: Path) -> None:
    import urllib.request

    print(f"[diarization] Downloading {url} ...")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, zip_path)
    print(f"[diarization] Extracting {zip_path.name} ...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_to.parent)
    zip_path.unlink(missing_ok=True)


def _parse_rttm(path: Path, uri: str) -> Annotation:
    annotation = Annotation(uri=uri)
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 8:
                continue
            start = float(parts[3])
            duration = float(parts[4])
            annotation[Segment(start, start + duration)] = parts[7]
    return annotation


def _segments_to_annotation(segments: list[dict], uri: str) -> Annotation:
    annotation = Annotation(uri=uri)
    for seg in segments:
        start = float(seg.get("start") or 0.0)
        end = float(seg.get("end") or 0.0)
        if end <= start:
            continue
        annotation[Segment(start, end)] = seg.get("speaker", "UNKNOWN")
    return annotation


def _post_audio(server_url: str, wav_path: Path) -> dict[str, Any]:
    url = f"{server_url.rstrip('/')}{ENDPOINT}"
    with open(wav_path, "rb") as f:
        resp = requests.post(url, files={"file": f}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def evaluate_diarization(
    server_url: str | None = None,
    data_dir: Path | None = None,
    subset_size: int | None = None,
    max_duration: float | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    _server_url = server_url or SERVER_URL
    _data_dir = data_dir or DEFAULT_DATA_DIR
    _subset_size = subset_size or SUBSET_SIZE
    _max_duration = max_duration or MAX_DURATION
    _report_path = report_path or (REPORTS_DIR / "diarization_report.json")

    thresholds = load_json(THRESHOLDS_PATH).get("diarization", {})
    _data_dir.mkdir(parents=True, exist_ok=True)

    audio_root, rttm_root = _ensure_dataset(_data_dir)
    wav_dir = audio_root / "voxconverse_test_wav"
    wav_files = sorted(wav_dir.glob("*.wav"))[:_subset_size]

    if not wav_files:
        print("[diarization] No WAV files found.", file=sys.stderr)
        report = {"component": "diarization", "metrics": {}, "thresholds": thresholds, "passed": False, "samples": []}
        write_json(_report_path, report)
        return report

    metric = DiarizationErrorRate()
    results: list[dict[str, Any]] = []
    times: list[float] = []

    print(f"[diarization] Evaluating {len(wav_files)} files against {_server_url} ...")

    for wav_path in wav_files:
        file_id = wav_path.stem
        rttm_path = rttm_root / RTTM_SUBDIR / f"{file_id}.rttm"

        if not rttm_path.exists():
            continue

        gt = _parse_rttm(rttm_path, file_id)
        data, sr = sf.read(str(wav_path))
        eval_dur = min(_max_duration, len(data) / sr)

        tmp_wav = Path(tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name)
        try:
            sf.write(str(tmp_wav), data[: int(eval_dur * sr)], sr)

            t0 = time.time()
            try:
                res = _post_audio(_server_url, tmp_wav)
            except Exception as exc:
                print(f"  [fail] {file_id}: {exc}", file=sys.stderr)
                continue
            elapsed = time.time() - t0

            segments = res.get("segments", [])
            if not segments:
                print(f"  [warn] {file_id}: empty segments", file=sys.stderr)
                continue

            hyp = _segments_to_annotation(segments, file_id)
            detail = metric(gt, hyp, uem=Timeline([Segment(0.0, eval_dur)]), detailed=True)
            total = detail["total"] if detail["total"] > 0 else 1.0

            results.append({
                "id": file_id,
                "der": round(detail["diarization error rate"], 4),
                "miss": round(detail["missed detection"] / total, 4),
                "fa": round(detail["false alarm"] / total, 4),
                "conf": round(detail["confusion"] / total, 4),
                "time_s": round(elapsed, 1),
            })
            times.append(elapsed)
        finally:
            tmp_wav.unlink(missing_ok=True)

    if not results:
        print("[diarization] No results. Check server.", file=sys.stderr)
        report = {"component": "diarization", "metrics": {}, "thresholds": thresholds, "passed": False, "samples": []}
        write_json(_report_path, report)
        return report

    g_detail = metric[:]
    g_total = g_detail["total"] if g_detail["total"] > 0 else 1.0
    metrics = {
        "overall_der": round(abs(metric), 4),
        "missed_detection_rate": round(g_detail["missed detection"] / g_total, 4),
        "false_alarm_rate": round(g_detail["false alarm"] / g_total, 4),
        "speaker_confusion_rate": round(g_detail["confusion"] / g_total, 4),
        "avg_processing_time_s": round(sum(times) / len(times), 2),
        "samples_evaluated": len(results),
    }

    passed = all(
        metrics[key] <= float(thresholds.get(thr, 1.0))
        for key, thr in [
            ("overall_der", "max_overall_der"),
            ("missed_detection_rate", "max_missed_detection_rate"),
            ("false_alarm_rate", "max_false_alarm_rate"),
            ("speaker_confusion_rate", "max_speaker_confusion_rate"),
        ]
    )

    report = {"component": "diarization", "metrics": metrics, "thresholds": thresholds, "passed": passed, "samples": results}
    write_json(_report_path, report)
    print(
        f"[diarization] passed={passed} "
        f"overall_der={metrics['overall_der']:.4f} "
        f"miss={metrics['missed_detection_rate']:.4f} "
        f"fa={metrics['false_alarm_rate']:.4f} "
        f"conf={metrics['speaker_confusion_rate']:.4f} "
        f"samples={metrics['samples_evaluated']}"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate pure diarization DER against VoxConverse benchmark.")
    parser.add_argument("--server-url", default=SERVER_URL, help=f"WhisperX service URL (default: {SERVER_URL})")
    parser.add_argument("--data-dir", type=Path, default=None, help="Directory to cache VoxConverse data (default: storage/eval_data/)")
    parser.add_argument("--subset-size", type=int, default=SUBSET_SIZE, help=f"Number of clips (default: {SUBSET_SIZE})")
    parser.add_argument("--max-duration", type=float, default=MAX_DURATION, help=f"Max clip duration in seconds (default: {MAX_DURATION})")
    parser.add_argument("--report", type=Path, default=None, help="Output report path")
    args = parser.parse_args()

    report = evaluate_diarization(
        server_url=args.server_url,
        data_dir=args.data_dir,
        subset_size=args.subset_size,
        max_duration=args.max_duration,
        report_path=args.report,
    )
    if not report["samples"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()