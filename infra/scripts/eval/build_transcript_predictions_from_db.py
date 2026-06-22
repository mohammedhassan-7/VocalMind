"""Build transcript predictions from the live pipeline's stored utterances.

Reads the diarized/transcribed utterances our pipeline produced for the 5 NexaLink
evaluation calls and emits a predictions file consumable by eval_transcript.py.
This measures real WER + speaker-role accuracy on our pipeline (no synthetic data).
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parents[3]
OUT_PATH = ROOT / "infra" / "benchmarks" / "fixtures" / "pipeline_predictions_live.json"

DSN = "postgresql://vocalmind:vocalmind_dev@localhost:5434/vocalmind"

# gold sample id -> processed interaction id (mapped via audio_file_path)
CALL_MAP = {
    "CALL_01_refund_outage": "13363006-5f7e-4119-ac27-ad3490544726",
    "CALL_02_billing_dispute_escalation": "cfee2635-1068-4651-b10e-b6ce4cc30f1d",
    "CALL_03_tech_support_slow_internet": "b83447b9-3a2c-4d8c-a1f5-c8bfcdfddf70",
    "CALL_04_access_recovery_fraud": "0f0e7df6-86a9-4d8b-92a0-5f162e8cc01f",
    "CALL_05_retention_abuse": "87b3f5e9-491d-4502-9573-37f60c31b293",
}


async def main() -> None:
    conn = await asyncpg.connect(DSN)
    samples = []
    try:
        for call_id, interaction_id in CALL_MAP.items():
            rows = await conn.fetch(
                """
                SELECT speaker_role::text AS speaker, text
                FROM utterances
                WHERE interaction_id = $1
                ORDER BY sequence_index
                """,
                interaction_id,
            )
            turns = [{"speaker": r["speaker"], "text": r["text"]} for r in rows]
            full_text = " ".join(r["text"] for r in rows)
            samples.append({"id": call_id, "text": full_text, "turns": turns})
            print(f"{call_id}: {len(turns)} turns, {len(full_text)} chars")
    finally:
        await conn.close()

    OUT_PATH.write_text(
        json.dumps({"transcript": {"samples": samples}}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
