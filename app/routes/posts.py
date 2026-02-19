from fastapi import APIRouter, Depends, HTTPException, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Post, SocialAccount, HashtagGroup
from app.routes import get_current_user, get_active_subscription
from typing import Any, Optional
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/posts", response_class=HTMLResponse)
async def list_posts(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription),
    tab: str = "all"
):
    query = db.query(Post).filter(Post.user_id == str(user.id))
    
    if tab == "drafts":
        query = query.filter(Post.status == "draft")
    elif tab == "scheduled":
        query = query.filter(Post.status == "scheduled")
    elif tab == "published":
        query = query.filter(Post.status == "published")
    elif tab == "failed":
        query = query.filter(Post.status == "failed")
    
    posts = query.order_by(desc(Post.updated_at)).all()
    
    return templates.TemplateResponse("posts/list.html", {
        "request": request, 
        "user": user, 
        "posts": posts,
        "tab": tab
    })

@router.get("/posts/new", response_class=HTMLResponse)
async def new_post_form(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == str(user.id)).all()
    hashtag_groups = db.query(HashtagGroup).filter(HashtagGroup.user_id == str(user.id)).all()
    return templates.TemplateResponse("posts/form.html", {
        "request": request, 
        "user": user,
        "accounts": accounts,
        "hashtag_groups": hashtag_groups
    })

@router.post("/posts/new")
async def create_post(
    request: Request,
    content: str = Form(...),
    account_id: int = Form(...),
    post_type: str = Form(...),
    post_status: str = Form("draft", alias="status"),
    media_urls: Optional[str] = Form(None),
    hashtags: Optional[str] = Form(None),
    scheduled_at: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    scheduled_dt = None
    if scheduled_at:
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_at)
        except ValueError:
            pass # Handle error or ignore
            
    new_post = Post(
        user_id=str(user.id),
        account_id=account_id,
        content=content,
        post_type=post_type,
        status=post_status,
        media_urls=media_urls,
        hashtags=hashtags,
        scheduled_at=scheduled_dt
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return RedirectResponse(url=f"/posts/{new_post.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/posts/{id}", response_class=HTMLResponse)
async def post_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    post = db.query(Post).filter(Post.id == id, Post.user_id == str(user.id)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("posts/detail.html", {"request": request, "user": user, "post": post})

@router.get("/posts/{id}/edit", response_class=HTMLResponse)
async def edit_post_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    post = db.query(Post).filter(Post.id == id, Post.user_id == str(user.id)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == str(user.id)).all()
    hashtag_groups = db.query(HashtagGroup).filter(HashtagGroup.user_id == str(user.id)).all()
    
    return templates.TemplateResponse("posts/form.html", {
        "request": request, 
        "user": user, 
        "post": post,
        "accounts": accounts,
        "hashtag_groups": hashtag_groups
    })

@router.post("/posts/{id}/edit")
async def update_post(
    request: Request,
    id: int,
    content: str = Form(...),
    account_id: int = Form(...),
    post_type: str = Form(...),
    post_status: str = Form(..., alias="status"),
    media_urls: Optional[str] = Form(None),
    hashtags: Optional[str] = Form(None),
    scheduled_at: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    post = db.query(Post).filter(Post.id == id, Post.user_id == str(user.id)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    scheduled_dt = None
    if scheduled_at:
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_at)
        except ValueError:
            pass

    post.content = content
    post.account_id = account_id
    post.post_type = post_type
    post.status = post_status
    post.media_urls = media_urls
    post.hashtags = hashtags
    post.scheduled_at = scheduled_dt
    
    db.commit()
    return RedirectResponse(url=f"/posts/{id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/posts/{id}/delete")
async def delete_post(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    post = db.query(Post).filter(Post.id == id, Post.user_id == str(user.id)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    return RedirectResponse(url="/posts", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/posts/{id}/publish")
async def publish_post(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    post = db.query(Post).filter(Post.id == id, Post.user_id == str(user.id)).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.status = "published"
    post.published_at = datetime.now()
    db.commit()
    return RedirectResponse(url=f"/posts/{id}", status_code=status.HTTP_303_SEE_OTHER)
