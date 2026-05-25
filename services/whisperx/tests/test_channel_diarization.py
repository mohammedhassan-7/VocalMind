from __future__ import annotations

import ast
import tempfile
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("soundfile")
import soundfile as sf


def _load_channel_helpers(force_agent_channel: int | None = None) -> tuple[callable, callable]:
    """Extract detect_stereo_layout + assign_speakers_by_channel from app.py.

    Mirrors the AST-exec pattern used by test_transcribe_pipeline.py so the
    test runs without importing whisperx / pyannote / fastapi.
    """
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    source = app_path.read_text(encoding="utf-8")
    module = ast.parse(source)
    targets = {"detect_stereo_layout", "assign_speakers_by_channel"}
    fn_sources = []
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name in targets:
            fn_sources.append(ast.get_source_segment(source, node))
    assert len(fn_sources) == 2, f"expected 2 functions, got {len(fn_sources)}"

    namespace: dict[str, object] = {
        "np": np,
        "Optional": __import__("typing").Optional,
        "List": list,
        "Dict": dict,
        "CHANNEL_DIARIZATION_ENABLED": True,
        "CHANNEL_DIARIZATION_MAX_CORR": 0.92,
        "FORCED_AGENT_CHANNEL": force_agent_channel,
    }
    for src in fn_sources:
        exec(src, namespace)  # noqa: S102 - controlled source from repo file
    return namespace["detect_stereo_layout"], namespace["assign_speakers_by_channel"]


def _write_stereo(path: str, ch0: np.ndarray, ch1: np.ndarray, sr: int = 16000) -> None:
    sf.write(path, np.stack([ch0, ch1], axis=1).astype(np.float32), sr)


def _write_mono(path: str, audio: np.ndarray, sr: int = 16000) -> None:
    sf.write(path, audio.astype(np.float32), sr)


@pytest.fixture
def synth_paths(tmp_path):
    rng = np.random.default_rng(42)
    sr = 16000
    agent = np.zeros(sr * 30, dtype=np.float32)
    agent[: sr * 5] = 0.3 * rng.standard_normal(sr * 5).astype(np.float32)
    agent[sr * 15 : sr * 18] = 0.25 * rng.standard_normal(sr * 3).astype(np.float32)
    customer = np.zeros(sr * 30, dtype=np.float32)
    customer[sr * 10 : sr * 14] = 0.35 * rng.standard_normal(sr * 4).astype(np.float32)

    stereo_path = str(tmp_path / "stereo_genuine.wav")
    _write_stereo(stereo_path, agent, customer, sr)

    reversed_path = str(tmp_path / "stereo_reversed.wav")
    _write_stereo(reversed_path, customer, agent, sr)

    mono_path = str(tmp_path / "mono.wav")
    _write_mono(mono_path, agent + customer, sr)

    dup_path = str(tmp_path / "stereo_duplicated.wav")
    _write_stereo(dup_path, agent + customer, agent + customer, sr)

    return {
        "stereo": stereo_path,
        "reversed": reversed_path,
        "mono": mono_path,
        "duplicated": dup_path,
        "sr": sr,
    }


def test_detect_stereo_layout_identifies_genuine_split_channel(synth_paths):
    detect, _ = _load_channel_helpers()
    layout = detect(synth_paths["stereo"])
    assert layout is not None
    assert layout["is_stereo_separated"] is True
    assert layout["agent_channel"] == 0
    assert layout["channels"] == 2
    assert layout["agent_source"] == "energy"


def test_detect_stereo_layout_returns_none_for_mono(synth_paths):
    detect, _ = _load_channel_helpers()
    assert detect(synth_paths["mono"]) is None


def test_detect_stereo_layout_returns_none_for_mono_duplicated_to_stereo(synth_paths):
    """High cross-correlation means the two channels carry the same signal —
    likely a mono file packed into a stereo container — and channel-mode
    diarization would give garbage. Must fall back to the cluster path."""
    detect, _ = _load_channel_helpers()
    assert detect(synth_paths["duplicated"]) is None


def test_detect_stereo_layout_picks_louder_channel_when_agent_is_on_right(synth_paths):
    detect, _ = _load_channel_helpers()
    layout = detect(synth_paths["reversed"])
    assert layout is not None
    assert layout["agent_channel"] == 1


def test_detect_stereo_layout_honors_forced_agent_channel_override(synth_paths):
    """Forced override must win over the energy heuristic for fixed-convention
    PBX deployments where channel assignment is known a priori."""
    detect, _ = _load_channel_helpers(force_agent_channel=1)
    layout = detect(synth_paths["stereo"])  # genuine: agent louder on ch0
    assert layout is not None
    assert layout["agent_channel"] == 1  # override beats energy
    assert layout["agent_source"] == "forced"


def test_assign_speakers_by_channel_labels_segments_by_energy(synth_paths):
    _, assign = _load_channel_helpers()
    segments = [
        {"start": 0.5, "end": 4.5, "speaker": "SPEAKER_00"},   # agent window
        {"start": 10.5, "end": 13.5, "speaker": "SPEAKER_00"},  # customer window
        {"start": 15.5, "end": 17.5, "speaker": "SPEAKER_00"},  # agent window
    ]
    out = assign(synth_paths["stereo"], segments, agent_channel=0)
    assert out[0]["speaker"] == "AGENT"
    assert out[1]["speaker"] == "CUSTOMER"
    assert out[2]["speaker"] == "AGENT"
    assert all(s["speaker_meta"]["strategy"] == "channel" for s in out)
    assert all(s["speaker_meta"]["agent_channel"] == 0 for s in out)
    assert all(0.0 <= s["speaker_meta"]["confidence"] <= 1.0 for s in out)


def test_assign_speakers_by_channel_skips_sub_50ms_segments(synth_paths):
    """Segments shorter than 50ms can't be measured reliably — they must keep
    their pre-channel labels rather than being relabeled from noise."""
    _, assign = _load_channel_helpers()
    segments = [
        {"start": 1.0, "end": 1.01, "speaker": "SPEAKER_00"},  # 10ms — skip
    ]
    out = assign(synth_paths["stereo"], segments, agent_channel=0)
    assert out[0]["speaker"] == "SPEAKER_00"
    assert "speaker_meta" not in out[0] or out[0].get("speaker_meta", {}).get("strategy") != "channel"


def test_assign_speakers_by_channel_falls_back_when_path_is_mono(synth_paths):
    """Mono input given to the channel-mode function (defensive — should not
    happen in practice) must leave segments unchanged rather than corrupting
    their existing labels."""
    _, assign = _load_channel_helpers()
    segments = [{"start": 0.5, "end": 4.5, "speaker": "SPEAKER_00"}]
    out = assign(synth_paths["mono"], segments, agent_channel=0)
    assert out[0]["speaker"] == "SPEAKER_00"


def test_assign_speakers_by_channel_falls_back_when_path_missing(tmp_path, capsys):
    """A bad path must fall back gracefully AND log — silent failure was the
    audit-flagged bug fixed in this PR; the test pins that fix."""
    _, assign = _load_channel_helpers()
    segments = [{"start": 0.5, "end": 4.5, "speaker": "SPEAKER_00"}]
    bogus = str(tmp_path / "does_not_exist.wav")
    out = assign(bogus, segments, agent_channel=0)
    assert out[0]["speaker"] == "SPEAKER_00"  # untouched
    captured = capsys.readouterr()
    assert "assign_speakers_by_channel" in captured.out  # logged, not silent
