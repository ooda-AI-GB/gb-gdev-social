from fastapi import APIRouter, Depends, HTTPException, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import ContentCalendar, Post
from app.routes import get_current_user, get_active_subscription
from typing import Any, Optional
from datetime import date, datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/calendar", response_class=HTMLResponse)
async def calendar_view(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    # Fetch all entries for user
    entries = db.query(ContentCalendar).filter(ContentCalendar.user_id == user.id).all()
    # Fetch all scheduled posts for user
    scheduled_posts = db.query(Post).filter(
        Post.user_id == user.id, 
        Post.status == "scheduled",
        Post.scheduled_at != None
    ).all()
    
    return templates.TemplateResponse("calendar/view.html", {
        "request": request, 
        "user": user, 
        "entries": entries,
        "scheduled_posts": scheduled_posts
    })

@router.get("/calendar/day/{date_str}", response_class=HTMLResponse)
async def calendar_day(
    request: Request,
    date_str: str,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    try:
        view_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
        
    entries = db.query(ContentCalendar).filter(
        ContentCalendar.user_id == user.id,
        ContentCalendar.date == view_date
    ).all()
    
    # Check for posts on this day
    # We need to filter by date part of datetime
    # SQLite has func.date, but we can do python filtering for simplicity or range query
    start_dt = datetime.combine(view_date, datetime.min.time())
    end_dt = datetime.combine(view_date, datetime.max.time())
    
    posts = db.query(Post).filter(
        Post.user_id == user.id,
        Post.scheduled_at >= start_dt,
        Post.scheduled_at <= end_dt
    ).all()
    
    return templates.TemplateResponse("calendar/day.html", {
        "request": request, 
        "user": user, 
        "date": view_date,
        "entries": entries,
        "posts": posts
    })

@router.post("/calendar/entry")
async def create_entry(
    request: Request,
    title: str = Form(...),
    date_str: str = Form(..., alias="date"),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    time_slot: Optional[str] = Form(None),
    color: str = Form("#6366f1"),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    entry_date = date.fromisoformat(date_str)
    
    new_entry = ContentCalendar(
        user_id=user.id,
        title=title,
        date=entry_date,
        category=category,
        description=description,
        time_slot=time_slot,
        color=color
    )
    db.add(new_entry)
    db.commit()
    return RedirectResponse(url="/calendar", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/calendar/entry/{id}/delete")
async def delete_entry(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    entry = db.query(ContentCalendar).filter(ContentCalendar.id == id, ContentCalendar.user_id == user.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    db.delete(entry)
    db.commit()
    return RedirectResponse(url="/calendar", status_code=status.HTTP_303_SEE_OTHER)
