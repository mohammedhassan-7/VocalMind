"""
Configuration module for VocalMind Final RAG.

Uses Pydantic Settings for type-safe config with .env file support.
Architecture:
  Parsing    → Docling  (AI-powered PDF → Markdown)
  Embeddings → Ollama   (snowflake-arctic-embed2, 1024-dim)
  Vector DB  → Qdrant   (dual collections: parents + children)
  LLM        → Groq     (fast cloud inference)
"""

from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

SERVICE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SERVICE_DIR.parent.parent


# ── Sub-configs ───────────────────────────────────────────────────────────────


class GroqConfig(BaseSettings):
    """Groq LLM configuration."""

    api_key: SecretStr = Field(alias="GROQ_API_KEY")
    model: str = Field(default="llama-3.3-70b-versatile", alias="LLM_MODEL")
    temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE")
    max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")
    context_window: int = 131_072


class EmbeddingConfig(BaseSettings):
    """Ollama embedding model configuration."""

    model: str = Field(default="snowflake-arctic-embed2", alias="EMBEDDING_MODEL")
    base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    dimension: int = Field(default=1024, alias="EMBEDDING_DIMENSION")
    request_timeout: float = 120.0


class QdrantConfig(BaseSettings):
    """Qdrant vector store configuration."""

    url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    collection_parents: str = Field(default="vocalmind_parents", alias="QDRANT_COLLECTION_PARENTS")
    collection_children: str = Field(default="vocalmind_children", alias="QDRANT_COLLECTION_CHILDREN")
    collection_sop_parents: str = Field(default="vocalmind_sop_parents", alias="QDRANT_COLLECTION_SOP_PARENTS")


class ParentChunkingConfig(BaseSettings):
    """Parent chunking: Markdown header splitting on H1/H2/H3."""

    headers_to_split_on: list[tuple[str, str]] = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    empty_section_min_words: int = 4


class ChildChunkingConfig(BaseSettings):
    """Child chunking: Recursive character splitting for precision snippets."""

    chunk_size: int = 400
    chunk_overlap: int = 80
    min_chunk_length: int = 30


# ── Main Settings ─────────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """Application-wide settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=(
            SERVICE_DIR / ".env",
            REPO_ROOT / ".env",
            REPO_ROOT / "backend" / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # Paths
    BASE_DIR: Path = SERVICE_DIR
    DOCS_DIR: Path = Field(
        default_factory=lambda: REPO_ROOT / "storage" / "docs",
        alias="DOCS_DIR",
    )
    PARSED_DIR: Path = Field(
        default_factory=lambda: REPO_ROOT / "storage" / "docs",
        alias="PARSED_DIR",
    )
    POLICY_DOCS_DIR: Path = Field(
        default_factory=lambda: REPO_ROOT / "storage" / "docs",
        alias="POLICY_DOCS_DIR",
    )
    KNOWLEDGE_DOCS_DIR: Path = Field(
        default_factory=lambda: REPO_ROOT / "storage" / "docs",
        alias="KNOWLEDGE_DOCS_DIR",
    )
    PARSED_POLICY_DIR: Path = Field(
        default_factory=lambda: REPO_ROOT / "storage" / "docs",
        alias="PARSED_POLICY_DIR",
    )
    PARSED_SOP_DIR: Path = Field(
        default_factory=lambda: REPO_ROOT / "storage" / "docs",
        alias="PARSED_SOP_DIR",
    )

    # ── Ollama Cloud (mirrors backend/app/core/config.py) ──
    LLM_PROVIDER: str = Field(default="groq", alias="LLM_PROVIDER")
    OLLAMA_CLOUD_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("OLLAMA_CLOUD_API_KEY", "OLLAMA_API_KEY"),
    )
    OLLAMA_CLOUD_BASE_URL: str = Field(
        default="https://ollama.com/v1",
        alias="OLLAMA_CLOUD_BASE_URL",
    )
    OLLAMA_CLOUD_HEAVY_MODEL: str = Field(
        default="kimi-k2.6:cloud",
        alias="OLLAMA_CLOUD_HEAVY_MODEL",
    )
    OLLAMA_CLOUD_FAST_MODEL: str = Field(
        default="ministral-3:8b",
        alias="OLLAMA_CLOUD_FAST_MODEL",
    )
    OLLAMA_MODEL_EMOTION_SHIFT: str = Field(default="", alias="OLLAMA_MODEL_EMOTION_SHIFT")
    OLLAMA_MODEL_PROCESS_ADHERENCE: str = Field(default="", alias="OLLAMA_MODEL_PROCESS_ADHERENCE")
    OLLAMA_MODEL_NLI_POLICY: str = Field(default="", alias="OLLAMA_MODEL_NLI_POLICY")
    OLLAMA_MODEL_RAG_JUDGE: str = Field(default="", alias="OLLAMA_MODEL_RAG_JUDGE")
    OLLAMA_MODEL_TEXT_TO_SQL: str = Field(default="", alias="OLLAMA_MODEL_TEXT_TO_SQL")
    OLLAMA_MODEL_FAST_CLASSIFICATION: str = Field(default="", alias="OLLAMA_MODEL_FAST_CLASSIFICATION")
    OLLAMA_MODEL_RAG_SYNTHESIS: str = Field(default="", alias="OLLAMA_MODEL_RAG_SYNTHESIS")
    # Legacy aliases retained for backward compatibility with older env files.
    OLLAMA_EMOTION_SHIFT_MODEL: str = Field(default="", alias="OLLAMA_EMOTION_SHIFT_MODEL")
    OLLAMA_PROCESS_ADHERENCE_MODEL: str = Field(default="", alias="OLLAMA_PROCESS_ADHERENCE_MODEL")
    OLLAMA_NLI_MODEL: str = Field(default="", alias="OLLAMA_NLI_MODEL")
    OLLAMA_CLOUD_EMBED_ENABLED: bool = Field(
        default=False,
        alias="OLLAMA_CLOUD_EMBED_ENABLED",
    )

    # Sub-configs
    groq: GroqConfig = Field(default_factory=GroqConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    parent_chunking: ParentChunkingConfig = Field(default_factory=ParentChunkingConfig)
    child_chunking: ChildChunkingConfig = Field(default_factory=ChildChunkingConfig)

    # Query defaults
    similarity_top_k: int = 5
    response_mode: Literal["compact", "refine", "tree_summarize"] = "compact"
    RAG_QUERY_LOG_ENABLED: bool = Field(default=False, alias="RAG_QUERY_LOG_ENABLED")

    def model_post_init(self, __context) -> None:
        """Resolve relative env paths from the RAG service directory."""
        self.DOCS_DIR = self._resolve_path(self.DOCS_DIR)
        self.PARSED_DIR = self._resolve_path(self.PARSED_DIR)
        self.POLICY_DOCS_DIR = self._resolve_path(self.POLICY_DOCS_DIR)
        self.KNOWLEDGE_DOCS_DIR = self._resolve_path(self.KNOWLEDGE_DOCS_DIR)
        self.PARSED_POLICY_DIR = self._resolve_path(self.PARSED_POLICY_DIR)
        self.PARSED_SOP_DIR = self._resolve_path(self.PARSED_SOP_DIR)

    @staticmethod
    def _resolve_path(path: Path) -> Path:
        """Resolve relative paths against services/rag/."""
        return path if path.is_absolute() else (SERVICE_DIR / path).resolve()

    def validate_config(self) -> None:
        """Validate critical config at startup."""
        if not self.DOCS_DIR.exists():
            raise ValueError(f"Docs directory {self.DOCS_DIR} does not exist.")


settings = Settings()


_HEAVY_STAGE = "heavy"
_FAST_STAGE = "fast"
# NOTE: fast_classification is benchmarked and configurable, but currently has
# no production runtime call site wired in backend/service flows.
_STAGE_MODEL_CLASS: dict[str, str] = {
    "emotion_shift": _HEAVY_STAGE,
    "process_adherence": _HEAVY_STAGE,
    "text_to_sql": _HEAVY_STAGE,
    "nli_policy": _FAST_STAGE,
    "rag_judge": _FAST_STAGE,
    "fast_classification": _FAST_STAGE,
    # rag_synthesis is intentionally unclassified for fast/heavy fallback:
    # when unset, it preserves legacy behavior by using settings.groq.model.
    "rag_synthesis": _FAST_STAGE,
}


def recognized_stage_names() -> tuple[str, ...]:
    """Expose recognized stage names for cross-service sync tests."""
    return tuple(sorted(_STAGE_MODEL_CLASS))


def resolve_model_for_stage(stage: str) -> str:
    """Resolve model for a named stage with staged + legacy fallbacks."""
    key = stage.lower().replace("-", "_")
    if key == "nli":
        key = "nli_policy"
    if key not in _STAGE_MODEL_CLASS:
        allowed = ", ".join(sorted(_STAGE_MODEL_CLASS))
        raise ValueError(f"Unknown LLM stage '{stage}'. Allowed stages: {allowed}")

    new_overrides = {
        "emotion_shift": settings.OLLAMA_MODEL_EMOTION_SHIFT,
        "process_adherence": settings.OLLAMA_MODEL_PROCESS_ADHERENCE,
        "nli_policy": settings.OLLAMA_MODEL_NLI_POLICY,
        "rag_judge": settings.OLLAMA_MODEL_RAG_JUDGE,
        "text_to_sql": settings.OLLAMA_MODEL_TEXT_TO_SQL,
        "fast_classification": settings.OLLAMA_MODEL_FAST_CLASSIFICATION,
        "rag_synthesis": settings.OLLAMA_MODEL_RAG_SYNTHESIS,
    }
    legacy_overrides = {
        "emotion_shift": settings.OLLAMA_EMOTION_SHIFT_MODEL,
        "process_adherence": settings.OLLAMA_PROCESS_ADHERENCE_MODEL,
        "nli_policy": settings.OLLAMA_NLI_MODEL,
    }

    stage_override = (new_overrides.get(key) or "").strip()
    if stage_override:
        return stage_override

    if key == "rag_synthesis":
        # No benchmark evidence for classifying synthesis as fast/heavy yet.
        # Preserve current behavior exactly when unset.
        return settings.groq.model

    legacy_override = (legacy_overrides.get(key) or "").strip()
    if legacy_override:
        return legacy_override

    if settings.LLM_PROVIDER == "ollama_cloud":
        if _STAGE_MODEL_CLASS[key] == _FAST_STAGE:
            return settings.OLLAMA_CLOUD_FAST_MODEL
        return settings.OLLAMA_CLOUD_HEAVY_MODEL
    return settings.groq.model


def rag_judge_model() -> str:
    """Model ID for RAG evaluator judge calls."""
    return resolve_model_for_stage("rag_judge")


def rag_synthesis_model() -> str:
    """Model ID for RAG synthesis calls in query_engine."""
    return resolve_model_for_stage("rag_synthesis")


def build_rag_llm_client():
    """
    OpenAI-compatible chat client for RAG judge calls.
    Groq SDK when LLM_PROVIDER=groq; OpenAI client → Ollama Cloud otherwise.
    """
    if settings.LLM_PROVIDER == "ollama_cloud":
        from openai import OpenAI

        api_key = settings.OLLAMA_CLOUD_API_KEY
        if not api_key:
            raise ValueError(
                "OLLAMA_CLOUD_API_KEY is not set. "
                "Set it in .env or keep LLM_PROVIDER=groq."
            )
        return OpenAI(
            api_key=api_key,
            base_url=settings.OLLAMA_CLOUD_BASE_URL,
        )
    from groq import Groq

    return Groq(api_key=settings.groq.api_key.get_secret_value())


def embedding_http_base_url() -> str:
    if settings.OLLAMA_CLOUD_EMBED_ENABLED:
        return settings.OLLAMA_CLOUD_BASE_URL.replace("/v1", "").rstrip("/")
    return settings.embedding.base_url.rstrip("/")


def embedding_http_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.OLLAMA_CLOUD_EMBED_ENABLED and settings.OLLAMA_CLOUD_API_KEY:
        headers["Authorization"] = f"Bearer {settings.OLLAMA_CLOUD_API_KEY}"
    return headers
