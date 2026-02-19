from fastapi import APIRouter, Depends, HTTPException, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import SocialAccount, AudienceSnapshot, Post
from app.routes import get_current_user, get_active_subscription
from typing import Any, Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/accounts", response_class=HTMLResponse)
async def list_accounts(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == str(user.id)).all()
    return templates.TemplateResponse("accounts/list.html", {"request": request, "user": user, "accounts": accounts})

@router.get("/accounts/new", response_class=HTMLResponse)
async def new_account_form(
    request: Request,
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    return templates.TemplateResponse("accounts/form.html", {"request": request, "user": user})

@router.post("/accounts/new")
async def create_account(
    request: Request,
    account_name: str = Form(...),
    platform: str = Form(...),
    account_id: Optional[str] = Form(None),
    avatar_url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    new_account = SocialAccount(
        user_id=str(user.id),
        platform=platform,
        account_name=account_name,
        account_id=account_id,
        avatar_url=avatar_url
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return RedirectResponse(url="/accounts", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/accounts/{id}", response_class=HTMLResponse)
async def account_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    account = db.query(SocialAccount).filter(SocialAccount.id == id, SocialAccount.user_id == str(user.id)).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Recent posts for this account
    recent_posts = db.query(Post).filter(
        Post.account_id == account.id,
        Post.status == "published"
    ).order_by(desc(Post.published_at)).limit(5).all()
    
    # Snapshots for charts
    snapshots = db.query(AudienceSnapshot).filter(
        AudienceSnapshot.account_id == account.id
    ).order_by(AudienceSnapshot.snapshot_date).all()
    
    return templates.TemplateResponse("accounts/detail.html", {
        "request": request, 
        "user": user, 
        "account": account,
        "recent_posts": recent_posts,
        "snapshots": snapshots
    })

@router.post("/accounts/{id}/edit")
async def update_account(
    request: Request,
    id: int,
    account_name: str = Form(...),
    platform: str = Form(...),
    account_id: Optional[str] = Form(None),
    avatar_url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    account = db.query(SocialAccount).filter(SocialAccount.id == id, SocialAccount.user_id == str(user.id)).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account.account_name = account_name
    account.platform = platform
    account.account_id = account_id
    account.avatar_url = avatar_url
    
    db.commit()
    return RedirectResponse(url=f"/accounts/{id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/accounts/{id}/delete")
async def delete_account(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    account = db.query(SocialAccount).filter(SocialAccount.id == id, SocialAccount.user_id == str(user.id)).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    db.delete(account)
    db.commit()
    return RedirectResponse(url="/accounts", status_code=status.HTTP_303_SEE_OTHER)
