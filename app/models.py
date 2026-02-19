from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    account_name = Column(String(100), nullable=False)
    account_id = Column(String, nullable=True)
    avatar_url = Column(Text, nullable=True)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    status = Column(String, default="connected")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    posts = relationship("Post", back_populates="account", cascade="all, delete-orphan")
    audience_snapshots = relationship("AudienceSnapshot", back_populates="account", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=False)
    content = Column(Text, nullable=False)
    media_urls = Column(Text, nullable=True)
    post_type = Column(String, nullable=False)
    status = Column(String, default="draft")
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    platform_post_id = Column(String, nullable=True)
    hashtags = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    account = relationship("SocialAccount", back_populates="posts")
    metrics = relationship("PostMetric", back_populates="post", uselist=False, cascade="all, delete-orphan")
    calendar_entries = relationship("ContentCalendar", back_populates="post")

class PostMetric(Base):
    __tablename__ = "post_metrics"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="metrics")

class ContentCalendar(Base):
    __tablename__ = "content_calendar"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    time_slot = Column(String, nullable=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    category = Column(String, nullable=False)
    color = Column(String, default="#6366f1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="calendar_entries")

class HashtagGroup(Base):
    __tablename__ = "hashtag_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    name = Column(String(100), nullable=False)
    hashtags = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    avg_reach = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AudienceSnapshot(Base):
    __tablename__ = "audience_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    top_post_type = Column(String, nullable=True)
    audience_growth = Column(Float, default=0.0)
    peak_hours = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("SocialAccount", back_populates="audience_snapshots")

class AIContentIdea(Base):
    __tablename__ = "ai_content_ideas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    platform = Column(String, nullable=True)
    idea_type = Column(String, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    tone = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
