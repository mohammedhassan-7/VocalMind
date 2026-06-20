from app.core import speaker_role_infer as sri


def test_relabel_enabled_model_unavailable_preserves_labels_and_warns(monkeypatch, caplog):
    segments = [
        {"text": "hello there", "speaker": "AGENT"},
        {"text": "need help with billing", "speaker": "CUSTOMER"},
    ]

    class _UnavailableClassifier:
        is_available = False

        def relabel_segments(self, incoming):
            return incoming

    monkeypatch.setattr("app.core.speaker_role_infer.settings.BACKEND_SPEAKER_RELABEL_ENABLED", True)
    monkeypatch.setattr("app.core.speaker_role_infer.settings.SPEAKER_ROLE_MODEL_DIR", "/tmp/nonexistent")
    monkeypatch.setattr(sri, "_classifier", _UnavailableClassifier())

    with caplog.at_level("WARNING"):
        out = sri.relabel_segments_with_speaker_model([dict(s) for s in segments])

    assert out == segments
    assert "model unavailable; WhisperX labels preserved unchanged" in caplog.text


def test_normalize_speaker_label_does_not_treat_cluster_ids_as_roles():
    assert sri._normalize_speaker_label("SPEAKER_00") is None
    assert sri._normalize_speaker_label("speaker_1") is None
