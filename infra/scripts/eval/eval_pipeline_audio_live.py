"""Measure real ASR WER + speaker-role accuracy of OUR pipeline.

Ground truth: the authored NexaLink call JSONs in storage/audio/nexalink/evaluation/
(these match the processed audio, including the recording-notice line).
Hypothesis:   the diarized/transcribed utterances our pipeline stored in the DB.

WER:   token-level Levenshtein over the full reference vs hypothesis transcript.
SPK:   word-level speaker-attribution accuracy. Reference and hypothesis token
       streams are tagged with their speaker, aligned with difflib, and matching
       tokens are scored on whether the pipeline assigned the right speaker.
"""
from __future__ import annotations

import asyncio
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parents[3]
EVAL_DIR = ROOT / "storage" / "audio" / "nexalink" / "evaluation"
DSN = "postgresql://vocalmind:vocalmind_dev@localhost:5434/vocalmind"

# gold call JSON (by CALL number) -> processed interaction id
CALL_MAP = {
    "CALL_01": "13363006-5f7e-4119-ac27-ad3490544726",
    "CALL_02": "cfee2635-1068-4651-b10e-b6ce4cc30f1d",
    "CALL_03": "b83447b9-3a2c-4d8c-a1f5-c8bfcdfddf70",
    "CALL_04": "0f0e7df6-86a9-4d8b-92a0-5f162e8cc01f",
    "CALL_05": "87b3f5e9-491d-4502-9573-37f60c31b293",
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def levenshtein(a: list[str], b: list[str]) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[-1]


def tagged_tokens(turns: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Flatten turns into (token, speaker) pairs."""
    out: list[tuple[str, str]] = []
    for speaker, text in turns:
        for tok in tokenize(text):
            out.append((tok, speaker))
    return out


def speaker_accuracy(ref: list[tuple[str, str]], hyp: list[tuple[str, str]]) -> tuple[int, int]:
    ref_tokens = [t for t, _ in ref]
    hyp_tokens = [t for t, _ in hyp]
    sm = SequenceMatcher(a=ref_tokens, b=hyp_tokens, autojunk=False)
    correct = total = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            continue
        for k in range(i2 - i1):
            total += 1
            if ref[i1 + k][1] == hyp[j1 + k][1]:
                correct += 1
    return correct, total


def load_reference(call_num: str) -> list[tuple[str, str]]:
    path = next(EVAL_DIR.glob(f"{call_num}_*.json"))
    data = json.loads(path.read_text(encoding="utf-8"))
    return [(t["speaker"].lower(), t["text"]) for t in data["turns"]]


async def load_hypothesis(conn: asyncpg.Connection, interaction_id: str) -> list[tuple[str, str]]:
    rows = await conn.fetch(
        "SELECT speaker_role::text AS s, text FROM utterances "
        "WHERE interaction_id = $1 ORDER BY sequence_index",
        interaction_id,
    )
    return [(r["s"].lower(), r["text"]) for r in rows]


async def main() -> None:
    conn = await asyncpg.connect(DSN)
    tot_edits = tot_ref = spk_correct = spk_total = 0
    print(f"{'call':<9} {'WER':>8} {'SPK-ACC':>9} {'ref_words':>10}")
    try:
        for call_num, interaction_id in CALL_MAP.items():
            ref_turns = load_reference(call_num)
            hyp_turns = await load_hypothesis(conn, interaction_id)

            ref_words = tokenize(" ".join(t for _, t in ref_turns))
            hyp_words = tokenize(" ".join(t for _, t in hyp_turns))
            edits = levenshtein(ref_words, hyp_words)
            tot_edits += edits
            tot_ref += len(ref_words)

            c, t = speaker_accuracy(tagged_tokens(ref_turns), tagged_tokens(hyp_turns))
            spk_correct += c
            spk_total += t

            wer = edits / len(ref_words) if ref_words else 0.0
            acc = c / t if t else 0.0
            print(f"{call_num:<9} {wer:>8.4f} {acc:>9.4f} {len(ref_words):>10}")
    finally:
        await conn.close()

    print("-" * 40)
    print(f"{'OVERALL':<9} {tot_edits / tot_ref:>8.4f} {spk_correct / spk_total:>9.4f} {tot_ref:>10}")
    print(f"\nWER            = {tot_edits / tot_ref * 100:.2f}%")
    print(f"Speaker-role   = {spk_correct / spk_total * 100:.2f}%")


if __name__ == "__main__":
    asyncio.run(main())
