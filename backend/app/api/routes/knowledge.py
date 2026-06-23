from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Path as FastAPIPath
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import select
from pypdf import PdfReader

from app.api.deps import SessionDep, CurrentUser
from app.core.config import settings
from app.core.knowledge_versioning import (
    activate_version,
    create_version,
    get_active_version,
    get_active_version_number,
    get_version_by_number,
    list_versions,
    snapshot_to_grounding,
)
from app.core.interaction_processing import (
    enqueue_interaction_processing,
    reset_interaction_for_reprocess,
)
from app.llm_trigger.service import evaluate_interaction_triggers
from app.models.enums import UserRole
from app.models.interaction import Interaction
from app.models.llm_trigger_cache import InteractionLLMTriggerCache
from app.models.organization import Organization
from app.models.policy import CompanyPolicy, OrganizationPolicy, PolicyCompliance
from app.models.faq import FAQArticle, OrganizationFAQArticle

router = APIRouter()


async def _record_kb_version(session: SessionDep, current_user: CurrentUser, summary: str) -> None:
    """Snapshot the org's knowledge into a new active version after a mutation.

    Called after each mutating knowledge endpoint commits. Editing knowledge
    deliberately does NOT invalidate cached session analysis — existing results
    are preserved with their original version tag; the new version only applies
    to interactions that are explicitly reprocessed.
    """
    await create_version(session, current_user.organization_id, current_user.id, summary)
    await session.commit()

POLICY_DOCS_FOLDER = "policy-docs"
SOP_DOCS_FOLDER = "sop-procedures"
LEGACY_FAQ_DOCS_FOLDER = "faq-docs"
KB_DOCS_FOLDER = "knowledge-base"
LEGACY_KB_DOCS_FOLDER = "kb"
KB_CATEGORY_PREFIX = "kb:"

# --- Schemas ---

class PolicyCreate(BaseModel):
    title: str = Field(..., description="The title of the company policy document.")
    category: str = Field(..., description="The category category of the policy (e.g. refunds, billing, compliance).")
    content: str = Field(..., description="The full markdown or plain text content of the policy.")

class PolicyUpdate(BaseModel):
    title: Optional[str] = Field(None, description="The updated title of the policy.")
    category: Optional[str] = Field(None, description="The updated category of the policy.")
    content: Optional[str] = Field(None, description="The updated content of the policy.")

class FAQCreate(BaseModel):
    question: str = Field(..., description="The question text for the FAQ article.")
    answer: str = Field(..., description="The detailed answer text for the FAQ article.")
    category: str = Field(..., description="The category category of the FAQ article.")

class FAQUpdate(BaseModel):
    question: Optional[str] = Field(None, description="The updated question text.")
    answer: Optional[str] = Field(None, description="The updated answer text.")
    category: Optional[str] = Field(None, description="The updated category of the FAQ.")


def _fallback_label(value: str | None, fallback: str) -> str:
    if value and value.strip():
        return value.strip()
    return fallback


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF") from exc

    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append(text)

    return "\n\n".join(pages).strip()


async def _get_org_slug(session: SessionDep, organization_id) -> str:
    result = await session.exec(select(Organization.slug).where(Organization.id == organization_id))
    slug = result.first()
    if not slug:
        raise HTTPException(status_code=404, detail="Organization not found")
    return slug


def _document_path(base_root: str, org_slug: str, folder_name: str, document_id: str) -> Path:
    return Path(base_root) / org_slug / folder_name / f"{document_id}.pdf"


async def _store_pdf_upload(
    session: SessionDep,
    current_user: CurrentUser,
    upload: UploadFile,
    base_root: str,
    folder_name: str,
    document_id: str,
) -> tuple[str, Path]:
    if not upload.filename or not upload.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await upload.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    org_slug = await _get_org_slug(session, current_user.organization_id)
    target_path = _document_path(base_root, org_slug, folder_name, document_id)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(file_bytes)
    return _extract_pdf_text(file_bytes), target_path


def _delete_document_file(base_root: str, org_slug: str, folder_name: str, document_id: str) -> None:
    target_path = _document_path(base_root, org_slug, folder_name, document_id)
    if target_path.exists():
        target_path.unlink()

# --- Endpoints ---


@router.get("/policies", responses={401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}})
async def list_policies(session: SessionDep, current_user: CurrentUser):
    """
    Retrieve all company policies with associated organization usage metrics.
    """
    # Subquery for compliance count
    count_stmt = (
        select(PolicyCompliance.policy_id, func.count(PolicyCompliance.id).label("usage_count"))
        .group_by(PolicyCompliance.policy_id)
        .subquery()
    )

    result = await session.exec(
        select(CompanyPolicy, OrganizationPolicy, count_stmt.c.usage_count)
        .join(OrganizationPolicy, OrganizationPolicy.policy_id == CompanyPolicy.id)
        .outerjoin(count_stmt, count_stmt.c.policy_id == CompanyPolicy.id)
        .where(OrganizationPolicy.organization_id == current_user.organization_id)
        .order_by(CompanyPolicy.policy_title)
    )
    
    policies_data = result.all()

    return [
        {
            "id": str(p.id),
            "documentType": "policy",
            "title": p.policy_title,
            "category": p.policy_category,
            "content": p.policy_text,
            "preview": p.policy_text[:60] + "..." if len(p.policy_text) > 60 else p.policy_text,
            "lastUpdated": p.updated_at.strftime("%Y-%m-%d") if p.updated_at else "",
            "isActive": op.is_active,
            "usageCount": usage_count or 0,
        }
        for p, op, usage_count in policies_data
    ]


@router.post("/policies", status_code=201, responses={401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}, 422: {"description": "Invalid input payload"}})
async def create_policy(session: SessionDep, current_user: CurrentUser, data: PolicyCreate):
    """
    Create a new company policy and assign it to the current organization.
    """
    policy = CompanyPolicy(
        organization_id=current_user.organization_id,
        policy_title=data.title,
        policy_category=data.category,
        policy_text=data.content,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    session.add(policy)
    await session.flush() # Get policy.id

    org_link = OrganizationPolicy(
        organization_id=current_user.organization_id,
        policy_id=policy.id,
        is_active=True
    )
    session.add(org_link)
    await session.commit()
    await _record_kb_version(session, current_user, f"Added policy '{policy.policy_title}'")
    return {"status": "success", "id": str(policy.id)}


@router.post("/policies/upload", status_code=201, responses={400: {"description": "Invalid PDF file"}, 401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}, 422: {"description": "Invalid form fields"}})
async def upload_policy(
    session: SessionDep,
    current_user: CurrentUser,
    title: str = Form(default="", description="The optional custom title for the policy document."),
    category: str = Form(default="Guidelines", description="The category category for the policy."),
    file: UploadFile = File(..., description="The PDF file containing the policy text to extract."),
):
    """
    Upload a PDF policy document and store its extracted text in the knowledge base.
    """
    policy_id = uuid4()
    extracted_text, _ = await _store_pdf_upload(
        session,
        current_user,
        file,
        settings.POLICY_DOCS_ROOT,
        POLICY_DOCS_FOLDER,
        str(policy_id),
    )
    policy = CompanyPolicy(
        id=policy_id,
        organization_id=current_user.organization_id,
        policy_title=_fallback_label(title, Path(file.filename or "policy").stem.replace("_", " ").title()),
        policy_category=_fallback_label(category, "Guidelines"),
        policy_text=extracted_text or _fallback_label(title, "Uploaded policy document"),
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(policy)
    await session.flush()

    org_link = OrganizationPolicy(
        organization_id=current_user.organization_id,
        policy_id=policy.id,
        is_active=True,
    )
    session.add(org_link)
    await session.commit()
    await _record_kb_version(session, current_user, f"Uploaded policy '{policy.policy_title}'")
    return {"status": "success", "id": str(policy.id)}


@router.patch("/policies/{policy_id}", responses={401: {"description": "Not authenticated"}, 403: {"description": "Access denied - not authorized to modify this policy"}, 404: {"description": "Policy not found"}, 422: {"description": "Invalid UUID format or input body"}})
async def update_policy(
    session: SessionDep,
    current_user: CurrentUser,
    policy_id: UUID = FastAPIPath(..., description="The unique UUID of the policy to update."),
    data: PolicyUpdate = None,
):
    """
    Update an existing company policy's title, category, or text content.
    """
    statement = select(CompanyPolicy).where(
        CompanyPolicy.id == policy_id,
        CompanyPolicy.organization_id == current_user.organization_id,
    )
    result = await session.exec(statement)
    policy = result.first()
    if not policy:
        raise HTTPException(status_code=403, detail="Not authorized to modify this policy")

    if data.title:
        policy.policy_title = data.title
    if data.category:
        policy.policy_category = data.category
    if data.content:
        policy.policy_text = data.content
    policy.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    session.add(policy)
    await session.commit()
    await _record_kb_version(session, current_user, f"Updated policy '{policy.policy_title}'")
    return {"status": "success"}


@router.patch("/policies/{policy_id}/upload", responses={400: {"description": "Invalid PDF file"}, 401: {"description": "Not authenticated"}, 403: {"description": "Access denied - not authorized to modify this policy"}, 404: {"description": "Policy not found"}, 422: {"description": "Invalid UUID or form fields"}})
async def replace_policy_upload(
    session: SessionDep,
    current_user: CurrentUser,
    policy_id: UUID = FastAPIPath(..., description="The unique UUID of the policy to replace."),
    title: str = Form(default="", description="The optional updated title of the policy."),
    category: str = Form(default="", description="The optional updated category of the policy."),
    file: UploadFile = File(..., description="The new PDF version of the policy document."),
):
    """
    Replace an existing policy with a newer PDF version and re-extract text.
    """
    statement = select(CompanyPolicy).where(
        CompanyPolicy.id == policy_id,
        CompanyPolicy.organization_id == current_user.organization_id,
    )
    result = await session.exec(statement)
    policy = result.first()
    if not policy:
        raise HTTPException(status_code=403, detail="Not authorized to modify this policy")

    extracted_text, _ = await _store_pdf_upload(
        session,
        current_user,
        file,
        settings.POLICY_DOCS_ROOT,
        POLICY_DOCS_FOLDER,
        str(policy_id),
    )

    policy.policy_title = _fallback_label(title, policy.policy_title)
    policy.policy_category = _fallback_label(category, policy.policy_category)
    policy.policy_text = extracted_text or policy.policy_text
    policy.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(policy)
    await session.commit()
    await _record_kb_version(session, current_user, f"Replaced policy '{policy.policy_title}'")
    return {"status": "success", "id": str(policy.id)}


@router.post("/policies/{policy_id}/toggle", responses={401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}, 404: {"description": "Policy assignment not found"}, 422: {"description": "Invalid UUID format"}})
async def toggle_policy(
    session: SessionDep,
    current_user: CurrentUser,
    policy_id: UUID = FastAPIPath(..., description="The unique UUID of the policy to toggle active status for."),
):
    """
    Toggle a policy's active status for the organization.
    """
    statement = select(OrganizationPolicy).where(
        OrganizationPolicy.organization_id == current_user.organization_id,
        OrganizationPolicy.policy_id == policy_id
    )
    result = await session.exec(statement)
    org_policy = result.first()
    if not org_policy:
        return {"status": "error", "message": "Assignment not found"}
    
    org_policy.is_active = not org_policy.is_active
    session.add(org_policy)
    await session.commit()
    _action = "Activated" if org_policy.is_active else "Deactivated"
    await _record_kb_version(session, current_user, f"{_action} a policy")
    return {"status": "success", "isActive": org_policy.is_active}


@router.get("/faqs", responses={401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}})
async def list_faqs(session: SessionDep, current_user: CurrentUser):
    """
    Retrieve all FAQ articles belonging to the organization.
    """
    result = await session.exec(
        select(FAQArticle, OrganizationFAQArticle)
        .join(OrganizationFAQArticle, OrganizationFAQArticle.article_id == FAQArticle.id)
        .where(
            OrganizationFAQArticle.organization_id == current_user.organization_id,
            ~FAQArticle.category.startswith(KB_CATEGORY_PREFIX),  # type: ignore[union-attr]
        )
        .order_by(FAQArticle.question)
    )
    faqs_data = result.all()

    return [
        {
            "id": str(f.id),
            "documentType": "faq",
            "question": f.question,
            "answer": f.answer,
            "preview": f.answer[:60] + "..." if len(f.answer) > 60 else f.answer,
            "category": f.category,
            "isActive": of.is_active,
            "usageCount": 0, # FAQs usage tracking not implemented yet
        }
        for f, of in faqs_data
    ]


@router.post("/faqs", status_code=201, responses={401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}, 422: {"description": "Invalid input payload"}})
async def create_faq(session: SessionDep, current_user: CurrentUser, data: FAQCreate):
    """
    Create a new FAQ article and assign it to the current organization.
    """
    faq = FAQArticle(
        organization_id=current_user.organization_id,
        question=data.question,
        answer=data.answer,
        category=data.category,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    session.add(faq)
    await session.flush()

    org_link = OrganizationFAQArticle(
        organization_id=current_user.organization_id,
        article_id=faq.id,
        is_active=True
    )
    session.add(org_link)
    await session.commit()
    await _record_kb_version(session, current_user, f"Added SOP '{faq.question}'")
    return {"status": "success", "id": str(faq.id)}


@router.post("/faqs/upload", status_code=201, responses={400: {"description": "Invalid PDF file"}, 401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}, 422: {"description": "Invalid form fields"}})
async def upload_faq(
    session: SessionDep,
    current_user: CurrentUser,
    question: str = Form(default="", description="The FAQ question text."),
    category: str = Form(default="Knowledge", description="The FAQ category."),
    file: UploadFile = File(..., description="The PDF file to extract the FAQ answer from."),
):
    """
    Upload a PDF FAQ article and store the extracted answer text in the knowledge base.
    """
    faq_id = uuid4()
    extracted_text, _ = await _store_pdf_upload(
        session,
        current_user,
        file,
        settings.KNOWLEDGE_DOCS_ROOT,
        SOP_DOCS_FOLDER,
        str(faq_id),
    )
    faq = FAQArticle(
        id=faq_id,
        organization_id=current_user.organization_id,
        question=_fallback_label(question, Path(file.filename or "faq").stem.replace("_", " ").title()),
        answer=extracted_text or _fallback_label(question, "Uploaded FAQ document"),
        category=_fallback_label(category, "Knowledge"),
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(faq)
    await session.flush()

    org_link = OrganizationFAQArticle(
        organization_id=current_user.organization_id,
        article_id=faq.id,
        is_active=True,
    )
    session.add(org_link)
    await session.commit()
    await _record_kb_version(session, current_user, f"Uploaded SOP '{faq.question}'")
    return {"status": "success", "id": str(faq.id)}


@router.patch("/faqs/{faq_id}", responses={401: {"description": "Not authenticated"}, 403: {"description": "Access denied - not authorized to modify this FAQ"}, 404: {"description": "FAQ not found"}, 422: {"description": "Invalid UUID format or input body"}})
async def update_faq(
    session: SessionDep,
    current_user: CurrentUser,
    faq_id: UUID = FastAPIPath(..., description="The unique UUID of the FAQ to update."),
    data: FAQUpdate = None,
):
    """
    Update an existing FAQ article's question, answer, or category.
    """
    statement = select(FAQArticle).where(
        FAQArticle.id == faq_id,
        FAQArticle.organization_id == current_user.organization_id,
    )
    result = await session.exec(statement)
    faq = result.first()
    if not faq:
        raise HTTPException(status_code=403, detail="Not authorized to modify this FAQ")

    if data.question:
        faq.question = data.question
    if data.answer:
        faq.answer = data.answer
    if data.category:
        faq.category = data.category
    faq.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    session.add(faq)
    await session.commit()
    await _record_kb_version(session, current_user, f"Updated SOP '{faq.question}'")
    return {"status": "success"}


@router.patch("/faqs/{faq_id}/upload", responses={400: {"description": "Invalid PDF file"}, 401: {"description": "Not authenticated"}, 403: {"description": "Access denied - not authorized to modify this FAQ"}, 404: {"description": "FAQ not found"}, 422: {"description": "Invalid UUID or form fields"}})
async def replace_faq_upload(
    session: SessionDep,
    current_user: CurrentUser,
    faq_id: UUID = FastAPIPath(..., description="The unique UUID of the FAQ to replace."),
    question: str = Form(default="", description="The optional updated question of the FAQ."),
    category: str = Form(default="", description="The optional updated category of the FAQ."),
    file: UploadFile = File(..., description="The new PDF version of the FAQ document."),
):
    """
    Replace an existing FAQ with a newer PDF version and re-extract text.
    """
    statement = select(FAQArticle).where(
        FAQArticle.id == faq_id,
        FAQArticle.organization_id == current_user.organization_id,
    )
    result = await session.exec(statement)
    faq = result.first()
    if not faq:
        raise HTTPException(status_code=403, detail="Not authorized to modify this FAQ")

    extracted_text, _ = await _store_pdf_upload(
        session,
        current_user,
        file,
        settings.KNOWLEDGE_DOCS_ROOT,
        SOP_DOCS_FOLDER,
        str(faq_id),
    )

    faq.question = _fallback_label(question, faq.question)
    faq.answer = extracted_text or faq.answer
    faq.category = _fallback_label(category, faq.category)
    faq.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(faq)
    await session.commit()
    await _record_kb_version(session, current_user, f"Replaced SOP '{faq.question}'")
    return {"status": "success", "id": str(faq.id)}


@router.post("/faqs/{faq_id}/toggle", responses={401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}, 404: {"description": "FAQ assignment not found"}, 422: {"description": "Invalid UUID format"}})
async def toggle_faq(
    session: SessionDep,
    current_user: CurrentUser,
    faq_id: UUID = FastAPIPath(..., description="The unique UUID of the FAQ to toggle active status for."),
):
    """
    Toggle an FAQ's active status for the organization.
    """
    statement = select(OrganizationFAQArticle).where(
        OrganizationFAQArticle.organization_id == current_user.organization_id,
        OrganizationFAQArticle.article_id == faq_id
    )
    result = await session.exec(statement)
    org_faq = result.first()
    if not org_faq:
        return {"status": "error", "message": "Assignment not found"}

    org_faq.is_active = not org_faq.is_active
    session.add(org_faq)
    await session.commit()
    _action = "Activated" if org_faq.is_active else "Deactivated"
    await _record_kb_version(session, current_user, f"{_action} an SOP")
    return {"status": "success", "isActive": org_faq.is_active}

@router.delete("/policies/{policy_id}", responses={401: {"description": "Not authenticated"}, 403: {"description": "Access denied - not authorized to delete this policy"}, 404: {"description": "Policy not found"}, 422: {"description": "Invalid UUID format"}})
async def delete_policy(
    session: SessionDep,
    current_user: CurrentUser,
    policy_id: UUID = FastAPIPath(..., description="The unique UUID of the policy to delete."),
):
    """
    Remove a policy from the organization's knowledge base.
    Only the policy's owning organization can delete it.
    """
    # Authorize via the organization's link to the policy — the same boundary
    # list_policies uses. A policy can be linked to an org while the underlying
    # CompanyPolicy.organization_id points at a different (e.g. seeded) owner, so
    # gating on CompanyPolicy.organization_id would 403 on policies the org sees.
    stmt = select(OrganizationPolicy).where(
        OrganizationPolicy.organization_id == current_user.organization_id,
        OrganizationPolicy.policy_id == policy_id,
    )
    res = await session.exec(stmt)
    org_policy = res.first()
    if not org_policy:
        raise HTTPException(status_code=403, detail="Not authorized to delete this policy")

    await session.delete(org_policy)

    # Remove the underlying policy only when no other organization still links
    # it, so deleting from one org's knowledge base never affects another org.
    remaining = (
        await session.exec(
            select(OrganizationPolicy).where(
                OrganizationPolicy.policy_id == policy_id,
                OrganizationPolicy.organization_id != current_user.organization_id,
            )
        )
    ).first()
    org_slug = await _get_org_slug(session, current_user.organization_id)
    if not remaining:
        policy = (
            await session.exec(select(CompanyPolicy).where(CompanyPolicy.id == policy_id))
        ).first()
        if policy:
            await session.delete(policy)
        _delete_document_file(settings.POLICY_DOCS_ROOT, org_slug, POLICY_DOCS_FOLDER, str(policy_id))

    await session.commit()
    await _record_kb_version(session, current_user, "Deleted a policy")
    return {"status": "success", "message": "Policy deleted"}


@router.delete("/faqs/{faq_id}", responses={401: {"description": "Not authenticated"}, 403: {"description": "Access denied - not authorized to delete this FAQ"}, 404: {"description": "FAQ not found"}, 422: {"description": "Invalid UUID format"}})
async def delete_faq(
    session: SessionDep,
    current_user: CurrentUser,
    faq_id: UUID = FastAPIPath(..., description="The unique UUID of the FAQ to delete."),
):
    """
    Remove an FAQ article from the organization's knowledge base.
    Only the FAQ's owning organization can delete it.
    """
    # Authorize via the organization's link (matches list_faqs visibility).
    stmt = select(OrganizationFAQArticle).where(
        OrganizationFAQArticle.organization_id == current_user.organization_id,
        OrganizationFAQArticle.article_id == faq_id,
    )
    res = await session.exec(stmt)
    org_faq = res.first()
    if not org_faq:
        raise HTTPException(status_code=403, detail="Not authorized to delete this FAQ")

    await session.delete(org_faq)

    # Delete the underlying article only when no other organization links it.
    remaining = (
        await session.exec(
            select(OrganizationFAQArticle).where(
                OrganizationFAQArticle.article_id == faq_id,
                OrganizationFAQArticle.organization_id != current_user.organization_id,
            )
        )
    ).first()
    org_slug = await _get_org_slug(session, current_user.organization_id)
    if not remaining:
        faq = (
            await session.exec(select(FAQArticle).where(FAQArticle.id == faq_id))
        ).first()
        if faq:
            await session.delete(faq)
        _delete_document_file(settings.KNOWLEDGE_DOCS_ROOT, org_slug, SOP_DOCS_FOLDER, str(faq_id))
        _delete_document_file(settings.KNOWLEDGE_DOCS_ROOT, org_slug, LEGACY_FAQ_DOCS_FOLDER, str(faq_id))
    await session.commit()
    await _record_kb_version(session, current_user, "Deleted an SOP")
    return {"status": "success", "message": "FAQ deleted"}


# --- Knowledge Base Endpoints ---


def _is_kb_article(faq: FAQArticle) -> bool:
    return (faq.category or "").startswith(KB_CATEGORY_PREFIX)


def _kb_display_category(raw_category: str) -> str:
    if raw_category.startswith(KB_CATEGORY_PREFIX):
        return raw_category[len(KB_CATEGORY_PREFIX):].strip() or "General"
    return raw_category


@router.get("/kb", responses={401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}})
async def list_kb_articles(session: SessionDep, current_user: CurrentUser):
    """
    List all knowledge base articles for the organization.
    """
    result = await session.exec(
        select(FAQArticle, OrganizationFAQArticle)
        .join(OrganizationFAQArticle, OrganizationFAQArticle.article_id == FAQArticle.id)
        .where(
            OrganizationFAQArticle.organization_id == current_user.organization_id,
            FAQArticle.category.startswith(KB_CATEGORY_PREFIX),  # type: ignore[union-attr]
        )
        .order_by(FAQArticle.question)
    )
    rows = result.all()
    return [
        {
            "id": str(faq.id),
            "documentType": "kb",
            "title": faq.question,
            "category": _kb_display_category(faq.category),
            "content": faq.answer,
            "preview": faq.answer[:60] + "..." if len(faq.answer) > 60 else faq.answer,
            "lastUpdated": faq.updated_at.strftime("%Y-%m-%d") if faq.updated_at else "",
            "isActive": org_link.is_active,
            "usageCount": 0,
        }
        for faq, org_link in rows
    ]


@router.post("/kb/upload", status_code=201, responses={400: {"description": "Invalid PDF file"}, 401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}, 422: {"description": "Invalid form parameters"}})
async def upload_kb_article(
    session: SessionDep,
    current_user: CurrentUser,
    title: str = Form(default="", description="The custom title for the KB article."),
    category: str = Form(default="General", description="The KB category/namespace."),
    file: UploadFile = File(..., description="The PDF file to extract knowledge base text from."),
):
    """
    Upload a PDF as a knowledge base article.
    """
    kb_id = uuid4()
    extracted_text, _ = await _store_pdf_upload(
        session,
        current_user,
        file,
        settings.KNOWLEDGE_DOCS_ROOT,
        KB_DOCS_FOLDER,
        str(kb_id),
    )
    faq = FAQArticle(
        id=kb_id,
        organization_id=current_user.organization_id,
        question=_fallback_label(title, Path(file.filename or "kb").stem.replace("_", " ").title()),
        answer=extracted_text or _fallback_label(title, "Uploaded KB document"),
        category=f"{KB_CATEGORY_PREFIX}{_fallback_label(category, 'General')}",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(faq)
    await session.flush()

    org_link = OrganizationFAQArticle(
        organization_id=current_user.organization_id,
        article_id=faq.id,
        is_active=True,
    )
    session.add(org_link)
    await session.commit()
    await _record_kb_version(session, current_user, f"Uploaded KB article '{faq.question}'")
    return {"status": "success", "id": str(faq.id)}


@router.patch("/kb/{kb_id}/upload", responses={400: {"description": "Invalid PDF file"}, 401: {"description": "Not authenticated"}, 403: {"description": "Access denied - not authorized to modify this KB article"}, 404: {"description": "KB article not found"}, 422: {"description": "Invalid UUID format or form parameters"}})
async def replace_kb_upload(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: UUID = FastAPIPath(..., description="The unique UUID of the KB article to replace."),
    title: str = Form(default="", description="The optional updated title of the KB article."),
    category: str = Form(default="", description="The optional updated category of the KB article."),
    file: UploadFile = File(..., description="The new PDF version of the KB article."),
):
    """
    Replace an existing KB article with a newer PDF version and re-extract text.
    """
    result = await session.exec(
        select(FAQArticle).where(
            FAQArticle.id == kb_id,
            FAQArticle.organization_id == current_user.organization_id,
        )
    )
    faq = result.first()
    if not faq or not _is_kb_article(faq):
        raise HTTPException(status_code=403, detail="Not authorized to modify this KB article")

    extracted_text, _ = await _store_pdf_upload(
        session,
        current_user,
        file,
        settings.KNOWLEDGE_DOCS_ROOT,
        KB_DOCS_FOLDER,
        str(kb_id),
    )
    faq.question = _fallback_label(title, faq.question)
    faq.answer = extracted_text or faq.answer
    if category.strip():
        faq.category = f"{KB_CATEGORY_PREFIX}{category.strip()}"
    faq.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(faq)
    await session.commit()
    await _record_kb_version(session, current_user, f"Replaced KB article '{faq.question}'")
    return {"status": "success", "id": str(faq.id)}


@router.post("/kb/{kb_id}/toggle", responses={401: {"description": "Not authenticated"}, 403: {"description": "Credentials invalid"}, 404: {"description": "KB article assignment not found"}, 422: {"description": "Invalid UUID format"}})
async def toggle_kb_article(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: UUID = FastAPIPath(..., description="The unique UUID of the KB article to toggle active status for."),
):
    """
    Toggle a KB article's active status.
    """
    result = await session.exec(
        select(OrganizationFAQArticle).where(
            OrganizationFAQArticle.organization_id == current_user.organization_id,
            OrganizationFAQArticle.article_id == kb_id,
        )
    )
    org_faq = result.first()
    if not org_faq:
        return {"status": "error", "message": "KB article not found"}
    org_faq.is_active = not org_faq.is_active
    session.add(org_faq)
    await session.commit()
    _action = "Activated" if org_faq.is_active else "Deactivated"
    await _record_kb_version(session, current_user, f"{_action} a KB article")
    return {"status": "success", "isActive": org_faq.is_active}


@router.delete("/kb/{kb_id}", responses={401: {"description": "Not authenticated"}, 403: {"description": "Access denied - not authorized to delete this KB article"}, 404: {"description": "KB article not found"}, 422: {"description": "Invalid UUID format"}})
async def delete_kb_article(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: UUID = FastAPIPath(..., description="The unique UUID of the KB article to delete."),
):
    """Remove a KB article from the organization. Only the owning org can delete it."""
    # Authorize via the organization's link (matches list_kb visibility).
    stmt = select(OrganizationFAQArticle).where(
        OrganizationFAQArticle.organization_id == current_user.organization_id,
        OrganizationFAQArticle.article_id == kb_id,
    )
    res = await session.exec(stmt)
    org_faq = res.first()
    if not org_faq:
        raise HTTPException(status_code=403, detail="Not authorized to delete this KB article")

    faq_entity = (
        await session.exec(select(FAQArticle).where(FAQArticle.id == kb_id))
    ).first()
    if not faq_entity or not _is_kb_article(faq_entity):
        raise HTTPException(status_code=403, detail="Not authorized to delete this KB article")

    await session.delete(org_faq)

    # Delete the underlying article only when no other organization links it.
    remaining = (
        await session.exec(
            select(OrganizationFAQArticle).where(
                OrganizationFAQArticle.article_id == kb_id,
                OrganizationFAQArticle.organization_id != current_user.organization_id,
            )
        )
    ).first()
    org_slug = await _get_org_slug(session, current_user.organization_id)
    if not remaining:
        await session.delete(faq_entity)
        _delete_document_file(settings.KNOWLEDGE_DOCS_ROOT, org_slug, KB_DOCS_FOLDER, str(kb_id))

    await session.commit()
    await _record_kb_version(session, current_user, "Deleted a KB article")
    return {"status": "success", "message": "KB article deleted"}


# --- Knowledge Versioning Endpoints (manager-only) ---


class ReprocessVersionRequest(BaseModel):
    interaction_ids: Optional[list[UUID]] = Field(
        default=None, description="Explicit interactions to reprocess. Omit to use `scope`."
    )
    scope: Optional[str] = Field(
        default=None, description="Set to 'stale' to reprocess all results tagged below the active version."
    )
    target: str = Field(
        default="active",
        description="'active' = judge against the current active version; 'original' = re-judge each result against the version it was first tagged with.",
    )


def _require_manager(current_user: CurrentUser) -> None:
    if current_user.role != UserRole.manager:
        raise HTTPException(status_code=403, detail="Knowledge versioning is only available to managers")


def _serialize_version(version, active_number: int) -> dict:
    return {
        "id": str(version.id),
        "versionNumber": version.version_number,
        "summary": version.summary,
        "createdBy": str(version.created_by) if version.created_by else None,
        "createdAt": version.created_at.isoformat() if version.created_at else None,
        "isActive": version.is_active,
        "isLatest": version.version_number == active_number,
    }


@router.get("/versions", responses={401: {"description": "Not authenticated"}, 403: {"description": "Manager role required"}})
async def list_knowledge_versions(session: SessionDep, current_user: CurrentUser):
    """List the organization's knowledge versions, newest first."""
    _require_manager(current_user)
    org_id = current_user.organization_id
    active_number = await get_active_version_number(session, org_id, current_user.id)
    await session.commit()  # persist any lazily-created baseline
    versions = await list_versions(session, org_id)
    return [_serialize_version(v, active_number) for v in versions]


@router.get("/versions/active", responses={401: {"description": "Not authenticated"}, 403: {"description": "Manager role required"}})
async def get_active_knowledge_version(session: SessionDep, current_user: CurrentUser):
    """Return the organization's currently active knowledge version."""
    _require_manager(current_user)
    org_id = current_user.organization_id
    await get_active_version_number(session, org_id, current_user.id)
    await session.commit()
    active = await get_active_version(session, org_id)
    return _serialize_version(active, active.version_number) if active else None


@router.post("/versions/{version_id}/activate", responses={401: {"description": "Not authenticated"}, 403: {"description": "Manager role required"}, 404: {"description": "Version not found"}})
async def activate_knowledge_version(
    session: SessionDep,
    current_user: CurrentUser,
    version_id: UUID = FastAPIPath(..., description="The knowledge version to restore and activate."),
):
    """Restore a previous version's knowledge snapshot and make it active.

    Existing analysis results are preserved with their original version tags; the
    restored knowledge only applies to interactions that are reprocessed.
    """
    _require_manager(current_user)
    try:
        version = await activate_version(session, current_user.organization_id, version_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Knowledge version not found")
    await session.commit()
    return {"status": "success", "activeVersion": version.version_number}


@router.post("/versions/reprocess", responses={401: {"description": "Not authenticated"}, 403: {"description": "Manager role required"}, 422: {"description": "No target interactions specified"}})
async def reprocess_against_version(
    session: SessionDep,
    current_user: CurrentUser,
    body: ReprocessVersionRequest,
):
    """Re-judge interactions' LLM analysis against a knowledge version.

    - ``target='active'`` runs the standard reprocess (re-tags to the active version).
    - ``target='original'`` re-judges each result against the snapshot it was first
      tagged with, leaving the active version unchanged.
    """
    _require_manager(current_user)
    org_id = current_user.organization_id
    org_slug = await _get_org_slug(session, org_id)
    active_number = await get_active_version_number(session, org_id, current_user.id)

    interaction_ids = await _resolve_reprocess_targets(session, org_id, body, active_number)
    if not interaction_ids:
        raise HTTPException(status_code=422, detail="No target interactions to reprocess")

    if body.target == "original":
        processed = await _reprocess_originals(session, org_id, org_slug, interaction_ids)
        await session.commit()
        return {"status": "success", "target": "original", "reprocessed": processed, "queued": False}

    # target == "active": full reprocess via the existing reset + enqueue path.
    for interaction_id in interaction_ids:
        await reset_interaction_for_reprocess(session, interaction_id)
    await session.commit()
    for interaction_id in interaction_ids:
        await enqueue_interaction_processing(interaction_id, priority=False)
    return {
        "status": "success",
        "target": "active",
        "activeVersion": active_number,
        "queued": True,
        "count": len(interaction_ids),
    }


async def _resolve_reprocess_targets(
    session: SessionDep, org_id: UUID, body: ReprocessVersionRequest, active_number: int
) -> list[UUID]:
    if body.interaction_ids:
        rows = (await session.exec(
            select(Interaction.id).where(
                Interaction.organization_id == org_id,
                Interaction.id.in_(body.interaction_ids),  # type: ignore[attr-defined]
            )
        )).all()
        return list(rows)
    if body.scope == "stale":
        rows = (await session.exec(
            select(InteractionLLMTriggerCache.interaction_id)
            .join(Interaction, Interaction.id == InteractionLLMTriggerCache.interaction_id)
            .where(
                Interaction.organization_id == org_id,
                InteractionLLMTriggerCache.knowledge_version.isnot(None),  # type: ignore[union-attr]
                InteractionLLMTriggerCache.knowledge_version < active_number,  # type: ignore[operator]
            )
        )).all()
        return list(rows)
    return []


async def _reprocess_originals(
    session: SessionDep, org_id: UUID, org_slug: str, interaction_ids: list[UUID]
) -> int:
    """Re-judge each interaction against its own originally-tagged version snapshot."""
    processed = 0
    for interaction_id in interaction_ids:
        tag = (await session.exec(
            select(InteractionLLMTriggerCache.knowledge_version).where(
                InteractionLLMTriggerCache.interaction_id == interaction_id
            )
        )).first()
        if tag is None:
            continue
        version = await get_version_by_number(session, org_id, tag)
        if version is None:
            continue
        policy_text, sop_text = snapshot_to_grounding(version.snapshot or {})
        try:
            await evaluate_interaction_triggers(
                session=session,
                interaction_id=interaction_id,
                retrieved_sop_from_pinecone=sop_text,
                ground_truth_policy=policy_text,
                org_filter=org_slug,
                requester_organization_id=org_id,
                force_rerun=True,
                commit_cache=False,
                force_persist=True,
                knowledge_version_override=tag,
            )
            processed += 1
        except Exception:
            continue
    return processed
