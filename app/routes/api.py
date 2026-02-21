from datetime import datetime, date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    AIContentIdea,
    AudienceSnapshot,
    ContentCalendar,
    HashtagGroup,
    Post,
    PostMetric,
    SocialAccount,
)
from app.routes import get_current_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_dict(obj) -> dict:
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        elif isinstance(val, date):
            val = val.isoformat()
        result[col.name] = val
    return result


def get_or_404(db: Session, model, id_val: int, label: str):
    obj = db.get(model, id_val)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return obj


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SocialAccountCreate(BaseModel):
    platform: str
    account_name: str
    account_id: Optional[str] = None
    avatar_url: Optional[str] = None
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    status: Optional[str] = "connected"


class SocialAccountUpdate(BaseModel):
    platform: Optional[str] = None
    account_name: Optional[str] = None
    account_id: Optional[str] = None
    avatar_url: Optional[str] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    status: Optional[str] = None


class PostCreate(BaseModel):
    account_id: int
    content: str
    media_urls: Optional[str] = None
    post_type: str
    status: Optional[str] = "draft"
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    platform_post_id: Optional[str] = None
    hashtags: Optional[str] = None


class PostUpdate(BaseModel):
    account_id: Optional[int] = None
    content: Optional[str] = None
    media_urls: Optional[str] = None
    post_type: Optional[str] = None
    status: Optional[str] = None
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    platform_post_id: Optional[str] = None
    hashtags: Optional[str] = None


class PostMetricCreate(BaseModel):
    post_id: int
    likes: Optional[int] = 0
    comments: Optional[int] = 0
    shares: Optional[int] = 0
    impressions: Optional[int] = 0
    reach: Optional[int] = 0
    clicks: Optional[int] = 0
    engagement_rate: Optional[float] = 0.0


class PostMetricUpdate(BaseModel):
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    impressions: Optional[int] = None
    reach: Optional[int] = None
    clicks: Optional[int] = None
    engagement_rate: Optional[float] = None


class ContentCalendarCreate(BaseModel):
    title: str
    date: str
    category: str
    description: Optional[str] = None
    time_slot: Optional[str] = None
    post_id: Optional[int] = None
    color: Optional[str] = "#6366f1"


class ContentCalendarUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    time_slot: Optional[str] = None
    post_id: Optional[int] = None
    color: Optional[str] = None


class HashtagGroupCreate(BaseModel):
    name: str
    hashtags: str
    category: Optional[str] = None
    avg_reach: Optional[int] = 0
    usage_count: Optional[int] = 0


class HashtagGroupUpdate(BaseModel):
    name: Optional[str] = None
    hashtags: Optional[str] = None
    category: Optional[str] = None
    avg_reach: Optional[int] = None
    usage_count: Optional[int] = None


class AudienceSnapshotCreate(BaseModel):
    account_id: int
    snapshot_date: str
    followers: Optional[int] = 0
    following: Optional[int] = 0
    engagement_rate: Optional[float] = 0.0
    top_post_type: Optional[str] = None
    audience_growth: Optional[float] = 0.0
    peak_hours: Optional[str] = None


class AudienceSnapshotUpdate(BaseModel):
    snapshot_date: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    engagement_rate: Optional[float] = None
    top_post_type: Optional[str] = None
    audience_growth: Optional[float] = None
    peak_hours: Optional[str] = None


class AIContentIdeaCreate(BaseModel):
    idea_type: str
    title: str
    content: str
    platform: Optional[str] = None
    tone: Optional[str] = None
    model_used: Optional[str] = None
    used: Optional[bool] = False


class AIContentIdeaUpdate(BaseModel):
    idea_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    tone: Optional[str] = None
    model_used: Optional[str] = None
    used: Optional[bool] = None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    user_id = str(user.id)
    total_accounts = db.query(SocialAccount).filter(SocialAccount.user_id == user_id).count()
    total_posts = db.query(Post).filter(Post.user_id == user_id).count()
    draft_posts = db.query(Post).filter(Post.user_id == user_id, Post.status == "draft").count()
    scheduled_posts = db.query(Post).filter(Post.user_id == user_id, Post.status == "scheduled").count()
    published_posts = db.query(Post).filter(Post.user_id == user_id, Post.status == "published").count()
    total_calendar_entries = db.query(ContentCalendar).filter(ContentCalendar.user_id == user_id).count()
    total_hashtag_groups = db.query(HashtagGroup).filter(HashtagGroup.user_id == user_id).count()
    total_ai_ideas = db.query(AIContentIdea).filter(AIContentIdea.user_id == user_id).count()
    used_ai_ideas = db.query(AIContentIdea).filter(AIContentIdea.user_id == user_id, AIContentIdea.used == True).count()

    account_ids = [
        row[0]
        for row in db.query(SocialAccount.id).filter(SocialAccount.user_id == user_id).all()
    ]
    total_audience_snapshots = (
        db.query(AudienceSnapshot).filter(AudienceSnapshot.account_id.in_(account_ids)).count()
        if account_ids else 0
    )
    post_ids = [
        row[0]
        for row in db.query(Post.id).filter(Post.user_id == user_id).all()
    ]
    total_post_metrics = (
        db.query(PostMetric).filter(PostMetric.post_id.in_(post_ids)).count()
        if post_ids else 0
    )

    return {
        "social_accounts": total_accounts,
        "posts": {
            "total": total_posts,
            "draft": draft_posts,
            "scheduled": scheduled_posts,
            "published": published_posts,
        },
        "content_calendar_entries": total_calendar_entries,
        "hashtag_groups": total_hashtag_groups,
        "ai_content_ideas": {
            "total": total_ai_ideas,
            "used": used_ai_ideas,
            "unused": total_ai_ideas - used_ai_ideas,
        },
        "audience_snapshots": total_audience_snapshots,
        "post_metrics": total_post_metrics,
    }


# ---------------------------------------------------------------------------
# SocialAccount CRUD
# ---------------------------------------------------------------------------

@router.get("/social-accounts")
def list_social_accounts(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    q = db.query(SocialAccount).filter(SocialAccount.user_id == str(user.id))
    if status:
        q = q.filter(SocialAccount.status == status)
    return [to_dict(a) for a in q.limit(limit).all()]


@router.get("/social-accounts/{account_id}")
def get_social_account(
    account_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, SocialAccount, account_id, "SocialAccount")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return to_dict(obj)


@router.post("/social-accounts", status_code=201)
def create_social_account(
    body: SocialAccountCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = SocialAccount(user_id=str(user.id), **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.put("/social-accounts/{account_id}")
def update_social_account(
    account_id: int,
    body: SocialAccountUpdate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, SocialAccount, account_id, "SocialAccount")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.delete("/social-accounts/{account_id}", status_code=204)
def delete_social_account(
    account_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, SocialAccount, account_id, "SocialAccount")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(obj)
    db.commit()


# ---------------------------------------------------------------------------
# Post CRUD
# ---------------------------------------------------------------------------

@router.get("/posts")
def list_posts(
    status: Optional[str] = Query(None),
    post_type: Optional[str] = Query(None),
    account_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    q = db.query(Post).filter(Post.user_id == str(user.id))
    if status:
        q = q.filter(Post.status == status)
    if post_type:
        q = q.filter(Post.post_type == post_type)
    if account_id is not None:
        q = q.filter(Post.account_id == account_id)
    return [to_dict(p) for p in q.limit(limit).all()]


@router.get("/posts/{post_id}")
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, Post, post_id, "Post")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return to_dict(obj)


@router.post("/posts", status_code=201)
def create_post(
    body: PostCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = Post(user_id=str(user.id), **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.put("/posts/{post_id}")
def update_post(
    post_id: int,
    body: PostUpdate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, Post, post_id, "Post")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, Post, post_id, "Post")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(obj)
    db.commit()


# ---------------------------------------------------------------------------
# PostMetric CRUD
# ---------------------------------------------------------------------------

@router.get("/post-metrics")
def list_post_metrics(
    post_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    user_post_ids = [
        row[0]
        for row in db.query(Post.id).filter(Post.user_id == str(user.id)).all()
    ]
    q = db.query(PostMetric).filter(PostMetric.post_id.in_(user_post_ids))
    if post_id is not None:
        q = q.filter(PostMetric.post_id == post_id)
    return [to_dict(m) for m in q.limit(limit).all()]


@router.get("/post-metrics/{metric_id}")
def get_post_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, PostMetric, metric_id, "PostMetric")
    post = db.get(Post, obj.post_id)
    if post is None or post.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return to_dict(obj)


@router.post("/post-metrics", status_code=201)
def create_post_metric(
    body: PostMetricCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    post = get_or_404(db, Post, body.post_id, "Post")
    if post.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    obj = PostMetric(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.put("/post-metrics/{metric_id}")
def update_post_metric(
    metric_id: int,
    body: PostMetricUpdate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, PostMetric, metric_id, "PostMetric")
    post = db.get(Post, obj.post_id)
    if post is None or post.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.delete("/post-metrics/{metric_id}", status_code=204)
def delete_post_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, PostMetric, metric_id, "PostMetric")
    post = db.get(Post, obj.post_id)
    if post is None or post.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(obj)
    db.commit()


# ---------------------------------------------------------------------------
# ContentCalendar CRUD
# ---------------------------------------------------------------------------

@router.get("/content-calendar")
def list_content_calendar(
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    q = db.query(ContentCalendar).filter(ContentCalendar.user_id == str(user.id))
    if category:
        q = q.filter(ContentCalendar.category == category)
    return [to_dict(e) for e in q.limit(limit).all()]


@router.get("/content-calendar/{entry_id}")
def get_content_calendar(
    entry_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, ContentCalendar, entry_id, "ContentCalendar")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return to_dict(obj)


@router.post("/content-calendar", status_code=201)
def create_content_calendar(
    body: ContentCalendarCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = ContentCalendar(user_id=str(user.id), **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.put("/content-calendar/{entry_id}")
def update_content_calendar(
    entry_id: int,
    body: ContentCalendarUpdate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, ContentCalendar, entry_id, "ContentCalendar")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.delete("/content-calendar/{entry_id}", status_code=204)
def delete_content_calendar(
    entry_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, ContentCalendar, entry_id, "ContentCalendar")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(obj)
    db.commit()


# ---------------------------------------------------------------------------
# HashtagGroup CRUD
# ---------------------------------------------------------------------------

@router.get("/hashtag-groups")
def list_hashtag_groups(
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    q = db.query(HashtagGroup).filter(HashtagGroup.user_id == str(user.id))
    if category:
        q = q.filter(HashtagGroup.category == category)
    return [to_dict(g) for g in q.limit(limit).all()]


@router.get("/hashtag-groups/{group_id}")
def get_hashtag_group(
    group_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, HashtagGroup, group_id, "HashtagGroup")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return to_dict(obj)


@router.post("/hashtag-groups", status_code=201)
def create_hashtag_group(
    body: HashtagGroupCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = HashtagGroup(user_id=str(user.id), **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.put("/hashtag-groups/{group_id}")
def update_hashtag_group(
    group_id: int,
    body: HashtagGroupUpdate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, HashtagGroup, group_id, "HashtagGroup")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.delete("/hashtag-groups/{group_id}", status_code=204)
def delete_hashtag_group(
    group_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, HashtagGroup, group_id, "HashtagGroup")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(obj)
    db.commit()


# ---------------------------------------------------------------------------
# AudienceSnapshot CRUD
# ---------------------------------------------------------------------------

@router.get("/audience-snapshots")
def list_audience_snapshots(
    account_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    user_account_ids = [
        row[0]
        for row in db.query(SocialAccount.id).filter(SocialAccount.user_id == str(user.id)).all()
    ]
    q = db.query(AudienceSnapshot).filter(AudienceSnapshot.account_id.in_(user_account_ids))
    if account_id is not None:
        q = q.filter(AudienceSnapshot.account_id == account_id)
    return [to_dict(s) for s in q.limit(limit).all()]


@router.get("/audience-snapshots/{snapshot_id}")
def get_audience_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, AudienceSnapshot, snapshot_id, "AudienceSnapshot")
    account = db.get(SocialAccount, obj.account_id)
    if account is None or account.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return to_dict(obj)


@router.post("/audience-snapshots", status_code=201)
def create_audience_snapshot(
    body: AudienceSnapshotCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    account = get_or_404(db, SocialAccount, body.account_id, "SocialAccount")
    if account.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    obj = AudienceSnapshot(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.put("/audience-snapshots/{snapshot_id}")
def update_audience_snapshot(
    snapshot_id: int,
    body: AudienceSnapshotUpdate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, AudienceSnapshot, snapshot_id, "AudienceSnapshot")
    account = db.get(SocialAccount, obj.account_id)
    if account is None or account.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.delete("/audience-snapshots/{snapshot_id}", status_code=204)
def delete_audience_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, AudienceSnapshot, snapshot_id, "AudienceSnapshot")
    account = db.get(SocialAccount, obj.account_id)
    if account is None or account.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(obj)
    db.commit()


# ---------------------------------------------------------------------------
# AIContentIdea CRUD
# ---------------------------------------------------------------------------

@router.get("/ai-content-ideas")
def list_ai_content_ideas(
    platform: Optional[str] = Query(None),
    idea_type: Optional[str] = Query(None),
    used: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    q = db.query(AIContentIdea).filter(AIContentIdea.user_id == str(user.id))
    if platform:
        q = q.filter(AIContentIdea.platform == platform)
    if idea_type:
        q = q.filter(AIContentIdea.idea_type == idea_type)
    if used is not None:
        q = q.filter(AIContentIdea.used == used)
    return [to_dict(i) for i in q.limit(limit).all()]


@router.get("/ai-content-ideas/{idea_id}")
def get_ai_content_idea(
    idea_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, AIContentIdea, idea_id, "AIContentIdea")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return to_dict(obj)


@router.post("/ai-content-ideas", status_code=201)
def create_ai_content_idea(
    body: AIContentIdeaCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = AIContentIdea(user_id=str(user.id), **body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.put("/ai-content-ideas/{idea_id}")
def update_ai_content_idea(
    idea_id: int,
    body: AIContentIdeaUpdate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, AIContentIdea, idea_id, "AIContentIdea")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return to_dict(obj)


@router.delete("/ai-content-ideas/{idea_id}", status_code=204)
def delete_ai_content_idea(
    idea_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    obj = get_or_404(db, AIContentIdea, idea_id, "AIContentIdea")
    if obj.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(obj)
    db.commit()
