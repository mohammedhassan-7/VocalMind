# Ingestion Pipeline

## Purpose

The ingestion pipeline converts policy and SOP PDFs into clean markdown and indexes them into Qdrant for retrieval.

Implementation: `services/rag/ingest.py`

## Inputs

Expected source structure under `DOCS_DIR` (`storage/docs`):

1. `storage/docs/{org}/policy-docs/*.pdf`
2. `storage/docs/{org}/sop-procedures/*.pdf`
3. `storage/docs/{org}/knowledge-base/*.pdf`

Legacy fallback:
1. `storage/docs/{org}/*.pdf`

## Outputs

For each processed file (per org):
1. Raw markdown: `storage/docs/{org}/parsed-docs/{file}_raw.md`
2. Clean markdown: `storage/docs/{org}/parsed-docs/{file}.md`
3. Chunk debug file: `storage/docs/{org}/parsed-docs/{file}_chunks.md`
4. Validation report: `storage/docs/{org}/parsed-docs/{file}_validation.json`
5. Qdrant Vectors:
   - `policy-docs` go to `vocalmind_parents` / `vocalmind_children`
   - `sop-procedures` go to `vocalmind_sop_parents` / `vocalmind_sop_children`
   - `knowledge-base` go to `vocalmind_sop_parents` (KB type)

Global run report:
1. `storage/docs/_pipeline_report.json`

## 8-Stage Pipeline

1. Parse PDF (Docling)
- `DocumentConverter` loads PDF and exports markdown

2. Clean markdown
- Encoding repair and table row repair

3. Extract metadata
- org, department, doc_id, version, effective_date
- `org` is overridden by folder name when available

4. Parent split
- Markdown header split on H1/H2/H3

5. Child split
- Recursive splitting for precision chunks
- Table chunks are kept atomic

6. Validate
- Flags short chunks and duplicate chunks

7. Save debug artifacts
- Writes chunk and validation diagnostics

8. Upload to Qdrant
- Embeds each chunk via Ollama
- Routes to `vocalmind_parents` if it is a policy document
- Routes to `vocalmind_sop_parents` if it is an SOP document

## Qdrant Behavior

1. Ensures collection existence
2. Recreates collections on embedding dimension mismatch
3. Uses deterministic IDs from content hashes for idempotent upserts

## Force Reindex

`force=True` deletes and recreates both collections before ingesting.

## CLI Usage

From `services/rag`:

```bash
python main.py --ingest
python main.py --ingest --force
```

## Operational Notes

1. Ensure Qdrant and Ollama are up before ingestion
2. Ensure `DOCS_DIR` points to `storage/docs`
3. Ensure `PARSED_DIR` points to `storage/docs`
4. Re-run ingestion whenever PDFs are added or updated

## Troubleshooting

1. No PDFs found
- Check folder names: `policy-docs`, `sop-procedures`
- Confirm files are `.pdf`

2. Empty or weak retrieval later
- Verify markdown artifacts exist in `storage/docs/{org}/parsed-docs`
- Confirm Qdrant collections contain points

3. Embedding errors
- Verify Ollama URL and model availability

4. Collection mismatch
- If dimension warnings appear, run force reindex

## Testing

Primary unit coverage is in:
1. `services/rag/tests/test_ingest.py`

Run:

```bash
cd services/rag
uv run pytest tests/test_ingest.py -q
```
