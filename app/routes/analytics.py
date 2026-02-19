from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models import Post, PostMetric, SocialAccount
from app.routes import get_current_user, get_active_subscription
from typing import Any, List
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_overview(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    # Total metrics across all accounts (basic summary)
    # Using python aggregation for simplicity, or complex SQL
    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == user.id).all()
    account_ids = [acc.id for acc in accounts]
    
    total_reach = 0
    total_impressions = 0
    total_engagement = 0
    total_clicks = 0
    
    # Get all metrics for posts belonging to these accounts
    # Join Post and PostMetric
    metrics = db.query(PostMetric).join(Post).filter(Post.account_id.in_(account_ids)).all()
    
    for m in metrics:
        total_reach += m.reach
        total_impressions += m.impressions
        total_engagement += (m.likes + m.comments + m.shares)
        total_clicks += m.clicks
        
    return templates.TemplateResponse("analytics/overview.html", {
        "request": request, 
        "user": user,
        "total_reach": total_reach,
        "total_impressions": total_impressions,
        "total_engagement": total_engagement,
        "total_clicks": total_clicks,
        "accounts": accounts
    })

@router.get("/api/analytics/metrics")
async def get_metrics(
    start: str = None, # YYYY-MM-DD
    end: str = None,
    account_id: int = None,
    platform: str = None,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    query = db.query(PostMetric).join(Post).filter(Post.user_id == user.id)
    
    if account_id:
        query = query.filter(Post.account_id == account_id)
    
    if platform:
        query = query.join(SocialAccount).filter(SocialAccount.platform == platform)
        
    if start:
        try:
            start_date = datetime.fromisoformat(start)
            query = query.filter(PostMetric.recorded_at >= start_date)
        except ValueError:
            pass
            
    if end:
        try:
            end_date = datetime.fromisoformat(end)
            query = query.filter(PostMetric.recorded_at <= end_date)
        except ValueError:
            pass
            
    metrics = query.order_by(PostMetric.recorded_at).all()
    
    # Return raw data for frontend to process into charts
    data = []
    for m in metrics:
        data.append({
            "date": m.recorded_at.isoformat(),
            "likes": m.likes,
            "comments": m.comments,
            "shares": m.shares,
            "impressions": m.impressions,
            "reach": m.reach,
            "engagement_rate": m.engagement_rate
        })
        
    return JSONResponse(content=data)

@router.get("/api/analytics/top-posts")
async def get_top_posts(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    # Join Post and Metric, order by engagement_rate
    results = db.query(Post, PostMetric).join(PostMetric).filter(
        Post.user_id == user.id
    ).order_by(desc(PostMetric.engagement_rate)).limit(limit).all()
    
    data = []
    for post, metric in results:
        data.append({
            "content": post.content[:50] + "...",
            "platform": post.account.platform if post.account else "unknown",
            "engagement_rate": metric.engagement_rate,
            "reach": metric.reach,
            "likes": metric.likes,
            "comments": metric.comments
        })
        
    return JSONResponse(content=data)
