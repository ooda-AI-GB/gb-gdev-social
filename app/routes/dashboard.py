from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Post, SocialAccount, AIContentIdea, ContentCalendar
from app.routes import get_current_user, get_active_subscription
from app.seed import seed_social_pro
from typing import Any
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    # Seed data check
    if db.query(SocialAccount).filter(SocialAccount.user_id == user.id).count() == 0:
        seed_social_pro(db, user.id)

    # Upcoming posts (next 7 days)
    now = datetime.now()
    next_week = now + timedelta(days=7)
    upcoming_posts = db.query(Post).filter(
        Post.user_id == user.id,
        Post.status == "scheduled",
        Post.scheduled_at >= now,
        Post.scheduled_at <= next_week
    ).order_by(Post.scheduled_at).all()

    # Recent performance (this implies checking metrics, but for dashboard maybe just some aggregates?)
    # "Recent performance metrics (total reach, engagement, followers gained this week)"
    # I'll just get total followers from accounts for now
    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == user.id).all()
    total_followers = sum(acc.followers_count for acc in accounts)
    
    # Latest AI ideas
    ai_ideas = db.query(AIContentIdea).filter(
        AIContentIdea.user_id == user.id,
        AIContentIdea.used == False
    ).order_by(desc(AIContentIdea.created_at)).limit(5).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "upcoming_posts": upcoming_posts,
        "total_followers": total_followers,
        "ai_ideas": ai_ideas,
        "accounts": accounts
    })
