# RAG Vector Retrieval Microservice

The RAG (Retrieval-Augmented Generation) system provides document ingestion, vector database management, and query adapters to ground LLM evaluations and assistant responses.

---

## 1. Core Architecture: Dual Collections

VocalMind utilizes Qdrant as its vector database, isolating documents across two distinct collections to optimize for different retrieval granularities:

| Collection | Granularity | Encodings | Primary Consumers |
| :--- | :--- | :--- | :--- |
| **`vocalmind_parents`** | Parent headers (H1/H2/H3 splits) | 1024-dim dense vectors (`snowflake-arctic-embed2`) | Compliance evaluations, NLI policy checks. Surfaced as *Provenance Cards*. |
| **`vocalmind_children`** | 400-character child segments with 80-character overlap | 1024-dim dense vectors (`snowflake-arctic-embed2`) | Text-to-SQL Manager Assistant Q&A answer synthesis (precise span quoting). |
| **`vocalmind_sop_parents`** | Parent header splits of SOP, KB, and procedure docs | 1024-dim dense vectors (`snowflake-arctic-embed2`) | SOP process-adherence checks and KB claim-validation lookups in LLM trigger chains. |

> [!NOTE]
> **Policy documents** are indexed at both parent (`vocalmind_parents`) and child (`vocalmind_children`) levels. **SOP and KB documents** are indexed only at parent level (`vocalmind_sop_parents`) — compliance evaluations need the entire rule with all conditions. The consumer type determines which collection to query: **parents/sop-parents** for compliance/SOP/KB, **children** for Q&A answer synthesis.

---

## 2. Ingestion Pipeline & CLI Commands

The ingestion pipeline parses PDFs, cleans text formatting, generates deterministic UUIDs using content hashing (ensuring duplicate uploads overwrite rather than double-index), embeds chunks using Ollama, and uploads them to Qdrant.

### Ingestion CLI commands
Ingestion is executed via the `services/rag/main.py` entry point:
*   **Full Ingestion**: Ingests new PDF documents.
    ```bash
    python main.py --ingest
    ```
*   **Force Re-ingest**: Wipes existing Qdrant collections and builds them fresh from source files.
    ```bash
    python main.py --ingest --force
    ```
*   **Document Watcher**: Continuously monitors the document directories, executing ingestion on file changes.
    ```bash
    python main.py --watch
    ```

---

## 3. Deep Dive References

For detailed guides on RAG subsystems, read the dedicated documentation:
*   **[RAG Retrieval Overview](../rag/RAG_OVERVIEW.md)**: Details vector layouts, similarity formulas, and runtime adapters.
*   **[RAG Ingestion Pipeline](../rag/INGESTION_PIPELINE.md)**: Details PDF parsing via Docling, text cleaning, chunking rules, and metadata generation.
