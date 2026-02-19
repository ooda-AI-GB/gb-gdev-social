from fastapi import APIRouter, Depends, HTTPException, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import HashtagGroup
from app.routes import get_current_user, get_active_subscription
from typing import Any, Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/hashtags", response_class=HTMLResponse)
async def list_hashtags(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    groups = db.query(HashtagGroup).filter(HashtagGroup.user_id == str(user.id)).all()
    return templates.TemplateResponse("hashtags/list.html", {"request": request, "user": user, "groups": groups})

@router.get("/hashtags/new", response_class=HTMLResponse)
async def new_hashtag_form(
    request: Request,
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    return templates.TemplateResponse("hashtags/form.html", {"request": request, "user": user})

@router.post("/hashtags/new")
async def create_hashtag_group(
    request: Request,
    name: str = Form(...),
    hashtags: str = Form(...), # Comma separated or just text
    category: Optional[str] = Form(None),
    avg_reach: Optional[int] = Form(0),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    new_group = HashtagGroup(
        user_id=str(user.id),
        name=name,
        hashtags=hashtags,
        category=category,
        avg_reach=avg_reach
    )
    db.add(new_group)
    db.commit()
    return RedirectResponse(url="/hashtags", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/hashtags/{id}/edit", response_class=HTMLResponse)
async def edit_hashtag_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    group = db.query(HashtagGroup).filter(HashtagGroup.id == id, HashtagGroup.user_id == str(user.id)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Hashtag Group not found")
    return templates.TemplateResponse("hashtags/form.html", {"request": request, "user": user, "group": group})

@router.post("/hashtags/{id}/edit")
async def update_hashtag_group(
    request: Request,
    id: int,
    name: str = Form(...),
    hashtags: str = Form(...),
    category: Optional[str] = Form(None),
    avg_reach: Optional[int] = Form(0),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    group = db.query(HashtagGroup).filter(HashtagGroup.id == id, HashtagGroup.user_id == str(user.id)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Hashtag Group not found")
    
    group.name = name
    group.hashtags = hashtags
    group.category = category
    group.avg_reach = avg_reach
    
    db.commit()
    return RedirectResponse(url="/hashtags", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/hashtags/{id}/delete")
async def delete_hashtag_group(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    group = db.query(HashtagGroup).filter(HashtagGroup.id == id, HashtagGroup.user_id == str(user.id)).first()
    if not group:
        raise HTTPException(status_code=404, detail="Hashtag Group not found")
    
    db.delete(group)
    db.commit()
    return RedirectResponse(url="/hashtags", status_code=status.HTTP_303_SEE_OTHER)
