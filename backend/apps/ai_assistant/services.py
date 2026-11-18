from typing import Literal
from django.conf import settings
from django.db.models import Q
from pydantic import BaseModel, Field

from apps.accounts.models import User
from apps.departments.models import Department
from apps.knowledge_base.services import recommend_articles_for_ticket
from apps.tickets.models import Ticket
from .gemini_client import GeminiQuotaExceededError, GeminiUnavailableError, generate_structured_json
from .models import AIRecommendation


class ClassificationSchema(BaseModel):
    category: Literal["HARDWARE", "SOFTWARE", "NETWORK", "ACCESS", "EMAIL", "SECURITY", "OTHER"]
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    department_code: str = Field(description="Matching department code from provided list, or empty string.")
    keywords: list[str] = Field(max_length=8)
    confidence_score: float = Field(ge=0.0, le=1.0)
    rationale: str


class SummarySchema(BaseModel):
    summary: str
    key_issues: list[str]
    current_status_assessment: str
    recommended_next_action: str


class TroubleshootingSchema(BaseModel):
    probable_root_cause: str
    troubleshooting_steps: list[str]
    verification_steps: list[str]


class SimilarTicketsSchema(BaseModel):
    similar_ticket_ids: list[int]
    reasoning: str


def _record_failed_recommendation(*, ticket: Ticket | None, user: User, rec_type: str, err: Exception) -> None:
    AIRecommendation.objects.create(
        ticket=ticket,
        requested_by=user,
        recommendation_type=rec_type,
        model_name=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
        status=AIRecommendation.Status.FAILED,
        error_message=str(err)[:1000],
    )


def classify_ticket_with_ai(*, user: User, title: str, description: str, ticket: Ticket | None = None) -> dict:
    departments = list(Department.objects.filter(is_active=True).values("id", "code", "name"))
    dept_context = ", ".join(f"{d['code']} ({d['name']})" for d in departments) or "None configured"

    prompt = (
        f"Classify this IT support request as a recommendation only.\n"
        f"Available Departments: {dept_context}\n"
        f"Title: {title}\n"
        f"Description: {description}"
    )
    system_instruction = (
        "You are an enterprise IT service desk triage assistant. "
        "Recommend the most appropriate category, priority, matching department_code, and technical keywords."
    )

    try:
        result: ClassificationSchema = generate_structured_json(
            system_instruction=system_instruction,
            prompt=prompt,
            response_schema=ClassificationSchema,
        )
    except (GeminiUnavailableError, GeminiQuotaExceededError) as exc:
        _record_failed_recommendation(
            ticket=ticket,
            user=user,
            rec_type=AIRecommendation.RecommendationType.CLASSIFICATION,
            err=exc,
        )
        raise

    matched_dept = next(
        (d for d in departments if d["code"].upper() == result.department_code.strip().upper()),
        None,
    )

    rec = AIRecommendation.objects.create(
        ticket=ticket,
        requested_by=user,
        recommendation_type=AIRecommendation.RecommendationType.CLASSIFICATION,
        suggested_category=result.category,
        suggested_priority=result.priority,
        suggested_department_id=matched_dept["id"] if matched_dept else None,
        keywords=result.keywords,
        summary_text=result.rationale,
        confidence_score=round(result.confidence_score, 3),
        model_name=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
        status=AIRecommendation.Status.COMPLETED,
    )

    return {
        "recommendation_id": rec.id,
        "is_advisory": True,
        "suggested_category": result.category,
        "suggested_priority": result.priority,
        "suggested_department": matched_dept,
        "keywords": result.keywords,
        "confidence_score": result.confidence_score,
        "rationale": result.rationale,
    }


def summarize_ticket_with_ai(*, user: User, ticket: Ticket) -> dict:
    comments = list(
        ticket.comments.select_related("author")
        .filter(is_internal=False if user.role == User.Role.EMPLOYEE else True)
        .order_by("created_at")[:30]
    ) if user.role == User.Role.EMPLOYEE else list(ticket.comments.select_related("author").order_by("created_at")[:30])

    comment_lines = "\n".join(
        f"- [{c.created_at.strftime('%Y-%m-%d %H:%M')}] {c.author.full_name} ({'Internal' if c.is_internal else 'Public'}): {c.body}"
        for c in comments
    ) or "No comments yet."

    prompt = (
        f"Ticket: {ticket.ticket_number} | Status: {ticket.status} | Priority: {ticket.priority}\n"
        f"Title: {ticket.title}\n"
        f"Description: {ticket.description}\n"
        f"Discussion History:\n{comment_lines}"
    )

    try:
        result: SummarySchema = generate_structured_json(
            system_instruction="Summarize the IT incident concisely for an IT support engineer or manager.",
            prompt=prompt,
            response_schema=SummarySchema,
        )
    except (GeminiUnavailableError, GeminiQuotaExceededError) as exc:
        _record_failed_recommendation(
            ticket=ticket,
            user=user,
            rec_type=AIRecommendation.RecommendationType.SUMMARY,
            err=exc,
        )
        raise

    AIRecommendation.objects.create(
        ticket=ticket,
        requested_by=user,
        recommendation_type=AIRecommendation.RecommendationType.SUMMARY,
        summary_text=result.summary,
        troubleshooting_steps=result.key_issues,
        model_name=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
        status=AIRecommendation.Status.COMPLETED,
    )

    return {
        "is_advisory": True,
        "ticket_number": ticket.ticket_number,
        "summary": result.summary,
        "key_issues": result.key_issues,
        "current_status_assessment": result.current_status_assessment,
        "recommended_next_action": result.recommended_next_action,
    }


def suggest_solutions_with_ai(*, user: User, ticket: Ticket) -> dict:
    kb_articles = recommend_articles_for_ticket(ticket=ticket, limit=5)
    kb_context = "\n".join(
        f"- [KB#{a.id}] {a.title}: {a.summary} | Steps: {a.troubleshooting_steps[:300]}"
        for a in kb_articles
    ) or "No matching internal knowledge base articles found."

    prompt = (
        f"Ticket: {ticket.ticket_number} ({ticket.category}, {ticket.priority})\n"
        f"Title: {ticket.title}\n"
        f"Description: {ticket.description}\n"
        f"Internal Knowledge Base Candidates:\n{kb_context}"
    )

    try:
        result: TroubleshootingSchema = generate_structured_json(
            system_instruction=(
                "Provide actionable troubleshooting recommendations for an IT support engineer. "
                "Reference relevant internal knowledge base guidance where helpful."
            ),
            prompt=prompt,
            response_schema=TroubleshootingSchema,
        )
    except (GeminiUnavailableError, GeminiQuotaExceededError) as exc:
        _record_failed_recommendation(
            ticket=ticket,
            user=user,
            rec_type=AIRecommendation.RecommendationType.TROUBLESHOOTING,
            err=exc,
        )
        raise

    article_ids = [a.id for a in kb_articles]
    AIRecommendation.objects.create(
        ticket=ticket,
        requested_by=user,
        recommendation_type=AIRecommendation.RecommendationType.TROUBLESHOOTING,
        summary_text=result.probable_root_cause,
        troubleshooting_steps=result.troubleshooting_steps,
        related_article_ids=article_ids,
        model_name=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
        status=AIRecommendation.Status.COMPLETED,
    )

    return {
        "is_advisory": True,
        "probable_root_cause": result.probable_root_cause,
        "troubleshooting_steps": result.troubleshooting_steps,
        "verification_steps": result.verification_steps,
        "recommended_articles": [
            {"id": a.id, "title": a.title, "category": a.category, "summary": a.summary}
            for a in kb_articles
        ],
    }


def find_similar_resolved_tickets(*, user: User, ticket: Ticket) -> dict:
    words = [w.strip(".,!?:;()[]{}\"'").lower() for w in ticket.title.split() if len(w) >= 4]
    query = Q(category=ticket.category)
    for w in words[:5]:
        query |= Q(title__icontains=w) | Q(description__icontains=w)

    candidates = list(
        Ticket.objects.filter(
            status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED],
        )
        .filter(query)
        .exclude(pk=ticket.pk)
        .order_by("-resolved_at")[:10]
    )

    if not candidates:
        return {"is_advisory": True, "similar_tickets": [], "reasoning": "No resolved tickets matched yet."}

    candidates_text = "\n".join(
        f"- ID={c.id} ({c.ticket_number}): {c.title} | Resolution: {c.resolution_notes[:200]}"
        for c in candidates
    )
    prompt = (
        f"Target Ticket: {ticket.title}\nDescription: {ticket.description}\n"
        f"Resolved Candidates:\n{candidates_text}"
    )

    try:
        result: SimilarTicketsSchema = generate_structured_json(
            system_instruction="Select up to 5 candidate IDs most similar to the target incident and explain briefly.",
            prompt=prompt,
            response_schema=SimilarTicketsSchema,
        )
        chosen_ids = set(result.similar_ticket_ids)
        ranked = [c for c in candidates if c.id in chosen_ids] or candidates[:3]
        reasoning = result.reasoning
    except (GeminiUnavailableError, GeminiQuotaExceededError) as exc:
        _record_failed_recommendation(
            ticket=ticket,
            user=user,
            rec_type=AIRecommendation.RecommendationType.SIMILAR_TICKETS,
            err=exc,
        )
        raise

    AIRecommendation.objects.create(
        ticket=ticket,
        requested_by=user,
        recommendation_type=AIRecommendation.RecommendationType.SIMILAR_TICKETS,
        summary_text=reasoning,
        similar_ticket_ids=[c.id for c in ranked],
        model_name=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
        status=AIRecommendation.Status.COMPLETED,
    )

    return {
        "is_advisory": True,
        "reasoning": reasoning,
        "similar_tickets": [
            {
                "id": c.id,
                "ticket_number": c.ticket_number,
                "title": c.title,
                "category": c.category,
                "priority": c.priority,
                "resolution_notes": c.resolution_notes,
                "resolved_at": c.resolved_at,
            }
            for c in ranked
        ],
    }
