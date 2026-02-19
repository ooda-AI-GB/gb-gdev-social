from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AIContentIdea
from app.routes import get_current_user, get_active_subscription
from typing import Any, Optional
import os
from google import genai

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_gemini_client():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

@router.get("/ai", response_class=HTMLResponse)
async def ai_studio(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    # Get recent ideas
    recent_ideas = db.query(AIContentIdea).filter(AIContentIdea.user_id == user.id).order_by(AIContentIdea.created_at.desc()).limit(10).all()
    has_api_key = os.environ.get("GOOGLE_API_KEY") is not None
    
    return templates.TemplateResponse("ai/studio.html", {
        "request": request, 
        "user": user, 
        "recent_ideas": recent_ideas,
        "has_api_key": has_api_key
    })

@router.post("/api/ai/generate")
async def generate_ideas(
    topic: str = Form(...),
    platform: str = Form(...),
    tone: str = Form("professional"),
    content_type: str = Form("post"),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    client = get_gemini_client()
    if not client:
        return JSONResponse({"error": "Google API Key not configured"}, status_code=500)
    
    prompt = f"Generate 3 {content_type} ideas for {platform} about '{topic}' with a {tone} tone. Return the response as JSON array of objects with 'title' and 'content' keys. Do not include markdown code blocks."
    
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text
        # Clean up markdown if present
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        import json
        ideas = json.loads(text)
        
        # Save to DB
        saved_ideas = []
        for idea in ideas:
            new_idea = AIContentIdea(
                user_id=user.id,
                platform=platform,
                idea_type=content_type,
                title=idea.get("title", "Untitled"),
                content=idea.get("content", ""),
                tone=tone,
                model_used="gemini-2.5-flash"
            )
            db.add(new_idea)
            saved_ideas.append({"title": new_idea.title, "content": new_idea.content})
            
        db.commit()
        return JSONResponse({"ideas": saved_ideas})
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/ai/caption")
async def write_caption(
    description: str = Form(...),
    platform: str = Form("instagram"),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    client = get_gemini_client()
    if not client:
         return JSONResponse({"error": "Google API Key not configured"}, status_code=500)
         
    prompt = f"Write a {platform} caption for a post about: {description}. Include emojis and hashtags."
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return JSONResponse({"caption": response.text})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/ai/hashtags")
async def research_hashtags(
    keyword: str = Form(...),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    client = get_gemini_client()
    if not client:
         return JSONResponse({"error": "Google API Key not configured"}, status_code=500)
         
    prompt = f"Suggest 30 hashtags for '{keyword}' categorized by reach (High, Medium, Low). Return as a JSON object with keys 'high_reach', 'medium_reach', 'low_reach', each containing an array of strings."
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text
         # Clean up markdown if present
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        import json
        data = json.loads(text)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/ai/repurpose")
async def repurpose_content(
    content: str = Form(...),
    target_platform: str = Form(...),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    client = get_gemini_client()
    if not client:
         return JSONResponse({"error": "Google API Key not configured"}, status_code=500)
    
    prompt = f"Repurpose the following content for {target_platform}. Make it native to the platform style.\n\nContent:\n{content}"
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return JSONResponse({"content": response.text})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
