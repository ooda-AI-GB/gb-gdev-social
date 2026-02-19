from sqlalchemy.orm import Session
from app.models import SocialAccount, Post, PostMetric, ContentCalendar, HashtagGroup, AudienceSnapshot, AIContentIdea
from datetime import datetime, timedelta, date
import json
import random

def seed_social_pro(db: Session, user_id: str):
    # Check if data already exists to avoid duplication
    if db.query(SocialAccount).filter(SocialAccount.user_id == user_id).first():
        return

    # 1. Create Accounts
    account1 = SocialAccount(
        user_id=user_id,
        platform="twitter",
        account_name="@acmebrand",
        followers_count=12400,
        following_count=890,
        status="connected",
        avatar_url="https://ui-avatars.com/api/?name=AB&background=1da1f2&color=fff"
    )
    account2 = SocialAccount(
        user_id=user_id,
        platform="instagram",
        account_name="@acme.official",
        followers_count=28700,
        following_count=1240,
        status="connected",
        avatar_url="https://ui-avatars.com/api/?name=AO&background=e4405f&color=fff"
    )
    db.add(account1)
    db.add(account2)
    db.commit()
    db.refresh(account1)
    db.refresh(account2)

    # 2. Audience Snapshots (Mar 2025 — Feb 2026)
    # Today is Feb 19 2026. So last 12 months.
    # Start from March 1st, 2025.
    start_date = date(2025, 3, 1)
    
    # Account 1 (Twitter): 8200 -> 12400, 2.1% -> 3.8%
    # Account 2 (Instagram): 15600 -> 28700, 3.4% -> 5.2%
    
    peak_hours = json.dumps(["09:00", "12:00", "17:00", "20:00"])
    
    for i in range(12):
        # Calculate date (1st of each month)
        year = 2025 + (3 + i - 1) // 12
        month = (3 + i - 1) % 12 + 1
        snapshot_date = date(year, month, 1)
        
        # Twitter linear growth
        followers1 = int(8200 + (12400 - 8200) * (i / 11))
        engagement1 = 2.1 + (3.8 - 2.1) * (i / 11)
        
        # Instagram linear growth
        followers2 = int(15600 + (28700 - 15600) * (i / 11))
        engagement2 = 3.4 + (5.2 - 3.4) * (i / 11)
        
        snap1 = AudienceSnapshot(
            account_id=account1.id,
            snapshot_date=snapshot_date,
            followers=followers1,
            following=890 + i*5,
            engagement_rate=round(engagement1, 2),
            top_post_type="text",
            audience_growth=2.5, # Dummy
            peak_hours=peak_hours
        )
        snap2 = AudienceSnapshot(
            account_id=account2.id,
            snapshot_date=snapshot_date,
            followers=followers2,
            following=1240 + i*10,
            engagement_rate=round(engagement2, 2),
            top_post_type="image",
            audience_growth=3.8, # Dummy
            peak_hours=peak_hours
        )
        db.add(snap1)
        db.add(snap2)

    # 3. Posts
    posts_data = [
        # Published
        {
            "account_id": account1.id, "content": "Excited to announce our new product line!", "post_type": "text", "status": "published",
            "published_at": datetime.now() - timedelta(days=5),
            "metrics": {"likes": 340, "comments": 45, "shares": 120, "impressions": 15200, "reach": 14000, "clicks": 200, "engagement_rate": 3.8}
        },
        {
            "account_id": account1.id, "content": "Behind the scenes at our design studio", "post_type": "text", "status": "published",
            "published_at": datetime.now() - timedelta(days=2),
            "metrics": {"likes": 210, "comments": 32, "shares": 65, "impressions": 8900, "reach": 8000, "clicks": 150, "engagement_rate": 3.4}
        },
        {
            "account_id": account2.id, "content": "New collection dropping Friday", "post_type": "image", "status": "published",
            "published_at": datetime.now() - timedelta(days=4),
            "media_urls": "https://placehold.co/600x400/e4405f/ffffff?text=New+Collection",
            "metrics": {"likes": 890, "comments": 124, "shares": 56, "impressions": 32100, "reach": 28000, "clicks": 500, "engagement_rate": 4.1}
        },
        {
            "account_id": account2.id, "content": "5 tips for sustainable living", "post_type": "carousel", "status": "published",
            "published_at": datetime.now() - timedelta(days=1),
            "media_urls": "https://placehold.co/600x400/e4405f/ffffff?text=Tip+1,https://placehold.co/600x400/e4405f/ffffff?text=Tip+2",
            "metrics": {"likes": 1240, "comments": 203, "shares": 312, "impressions": 45600, "reach": 40000, "clicks": 800, "engagement_rate": 4.8}
        },
        # Scheduled
        {
            "account_id": account1.id, "content": "Big announcement coming next week! Stay tuned", "post_type": "text", "status": "scheduled",
            "scheduled_at": datetime.now() + timedelta(days=3)
        },
        {
            "account_id": account2.id, "content": "Quick tutorial: 3 ways to style our bestseller", "post_type": "video", "status": "scheduled",
            "scheduled_at": datetime.now() + timedelta(days=5)
        },
        # Drafts
        {
            "account_id": account1.id, "content": "Thread: Why we're doubling down on sustainability in 2026", "post_type": "text", "status": "draft"
        },
        {
            "account_id": account2.id, "content": "Poll: Which color should we launch next?", "post_type": "story", "status": "draft"
        }
    ]

    for p_data in posts_data:
        metrics_data = p_data.pop("metrics", None)
        post = Post(user_id=user_id, **p_data)
        db.add(post)
        db.flush() # get ID
        
        if metrics_data:
            metric = PostMetric(post_id=post.id, **metrics_data)
            db.add(metric)
            
            # Also add to calendar if it's a post
            # "Create 5 seed content calendar entries..." - wait, these are separate from posts, or linked?
            # "post_id: int — optional, foreign key to posts.id (linked post)"
            # I'll link published/scheduled posts to calendar automatically or just follow the specific calendar seed instructions.
            # The prompt has specific calendar entries. I'll do those separately.

    # 4. Hashtag Groups
    hashtags_data = [
        {"name": "Brand Core", "category": "branded", "hashtags": json.dumps(["#AcmeBrand", "#AcmeLife", "#BuiltByAcme", "#AcmeStyle"]), "avg_reach": 5200},
        {"name": "Industry Trending", "category": "trending", "hashtags": json.dumps(["#Sustainability", "#EcoFriendly", "#GreenBusiness", "#CircularEconomy", "#NetZero"]), "avg_reach": 45000},
        {"name": "Engagement Boosters", "category": "engagement", "hashtags": json.dumps(["#MondayMotivation", "#TipTuesday", "#ThrowbackThursday", "#FeatureFriday", "#WeekendVibes"]), "avg_reach": 120000}
    ]
    for h_data in hashtags_data:
        group = HashtagGroup(user_id=user_id, **h_data)
        db.add(group)

    # 5. Content Calendar (current month)
    # 5 entries
    current_month = date.today().replace(day=1)
    calendar_data = [
        {"title": "Product Launch Post", "category": "announcement", "color": "#ef4444", "date": current_month.replace(day=5)},
        {"title": "Customer Spotlight", "category": "user_generated", "color": "#6366f1", "date": current_month.replace(day=12)},
        {"title": "Industry Tips Thread", "category": "educational", "color": "#10b981", "date": current_month.replace(day=18)},
        {"title": "Flash Sale Promo", "category": "promotional", "color": "#f59e0b", "date": current_month.replace(day=24)},
        {"title": "Team Photo Friday", "category": "behind_scenes", "color": "#8b5cf6", "date": current_month.replace(day=28)} # Might fail for Feb, handle carefully
    ]
    
    # Handle Feb 28/Leap year or just safe days
    # I'll just use safe days (1, 5, 10, 15, 20) relative to today or start of month
    
    for i, c_data in enumerate(calendar_data):
        # Adjust date to be safe
        c_data["date"] = current_month.replace(day=3 + i*5)
        entry = ContentCalendar(user_id=user_id, **c_data)
        db.add(entry)

    # 6. AI Content Ideas
    ai_data = [
        {"idea_type": "hook", "platform": "twitter", "title": "Contrarian Industry Take", "content": "Everyone says X about sustainability. Here's why they're wrong (and what the data actually shows)...", "tone": "professional"},
        {"idea_type": "caption", "platform": "instagram", "title": "Product Feature Spotlight", "content": "The little details matter. Swipe to see the 3 features our customers love most about [Product]. Which one's your favorite? Drop a comment below 👇", "tone": "casual"},
        {"idea_type": "thread", "platform": "twitter", "title": "Behind the Numbers", "content": "We grew 40% this quarter. But the vanity metrics aren't the real story. Here's what actually moved the needle (thread) 🧵", "tone": "inspirational"}
    ]
    for a_data in ai_data:
        idea = AIContentIdea(user_id=user_id, **a_data)
        db.add(idea)

    db.commit()
