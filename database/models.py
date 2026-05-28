import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from .connection import Base


class User(Base):
    """
    User account for ARIA login.

    Columns:
        id             — UUID primary key
        email          — unique login email
        hashed_password— bcrypt hash (never store plain text!)
        full_name      — display name (optional)
        is_active      — False = account disabled
        created_at     — registration timestamp
        last_login     — last successful login (nullable)
    """
    __tablename__ = "users"

    id              = Column(String,   primary_key=True, default=lambda: str(uuid.uuid4()))
    email           = Column(String,   unique=True, nullable=False, index=True)
    hashed_password = Column(String,   nullable=False)
    full_name       = Column(String,   nullable=True)
    is_active       = Column(Boolean,  default=True, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login      = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id             = Column(String,   primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id        = Column(String,   ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic          = Column(String,   nullable=False)
    content        = Column(Text,     nullable=False)
    images         = Column(JSON,     nullable=False, default=list)
    word_count     = Column(Integer,  default=0)
    chroma_post_id = Column(String,   nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<BlogPost id={self.id} user_id={self.user_id} topic={self.topic!r}>"
