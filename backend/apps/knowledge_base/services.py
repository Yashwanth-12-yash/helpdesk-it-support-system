import uuid
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import User
from apps.tickets.models import Ticket
from .models import KnowledgeArticle


def _generate_unique_slug(title: str) -> str:
    base = slugify(title)[:220] or "article"
    slug = base
    while KnowledgeArticle.objects.filter(slug=slug).exists():
        slug = f"{base[:200]}-{uuid.uuid4().hex[:6]}"
    return slug


@transaction.atomic
def create_article(*, author: User, **validated_data) -> KnowledgeArticle:
    slug = _generate_unique_slug(validated_data["title"])
    status_val = validated_data.pop("status", KnowledgeArticle.Status.DRAFT)
    if author.role == User.Role.ENGINEER and status_val == KnowledgeArticle.Status.PUBLISHED:
        status_val = KnowledgeArticle.Status.DRAFT

    article = KnowledgeArticle.objects.create(
        slug=slug,
        author=author,
        status=status_val,
        published_by=author if status_val == KnowledgeArticle.Status.PUBLISHED else None,
        published_at=timezone.now() if status_val == KnowledgeArticle.Status.PUBLISHED else None,
        **validated_data,
    )
    return article


@transaction.atomic
def update_article(*, article: KnowledgeArticle, actor: User, **validated_data) -> KnowledgeArticle:
    for field, value in validated_data.items():
        setattr(article, field, value)
    article.save()
    return article


@transaction.atomic
def publish_article(*, article: KnowledgeArticle, actor: User) -> KnowledgeArticle:
    article.status = KnowledgeArticle.Status.PUBLISHED
    article.published_by = actor
    article.published_at = timezone.now()
    article.save(update_fields=["status", "published_by", "published_at", "updated_at"])
    return article


@transaction.atomic
def archive_article(*, article: KnowledgeArticle) -> KnowledgeArticle:
    article.status = KnowledgeArticle.Status.ARCHIVED
    article.save(update_fields=["status", "updated_at"])
    return article


def increment_article_views(article: KnowledgeArticle) -> None:
    KnowledgeArticle.objects.filter(pk=article.pk).update(view_count=F("view_count") + 1)


def recommend_articles_for_ticket(*, ticket: Ticket, limit: int = 5):
    """Recommend published KB articles matching ticket category and title keywords."""
    words = [w.strip(".,!?:;()[]{}\"'").lower() for w in ticket.title.split() if len(w) >= 4]
    qs = KnowledgeArticle.objects.filter(status=KnowledgeArticle.Status.PUBLISHED)

    keyword_q = Q(category=ticket.category)
    for word in words[:6]:
        keyword_q |= Q(title__icontains=word) | Q(summary__icontains=word)

    matches = list(qs.filter(keyword_q).order_by("-view_count")[:limit])
    if len(matches) < limit:
        existing_ids = [a.id for a in matches]
        fallback = list(
            qs.filter(category=ticket.category).exclude(id__in=existing_ids).order_by("-view_count")[: limit - len(matches)]
        )
        matches.extend(fallback)
    return matches
