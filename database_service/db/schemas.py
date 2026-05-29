"""
SQLModel-модели для описания таблиц в базе данных.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Registration(SQLModel, table=True):
    """Таблица 'registrations' в PostgreSQL."""
    
    __tablename__ = "registrations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    registration_id: str = Field(unique=True, index=True, min_length=1, max_length=100)
    event_name: str = Field(min_length=1, max_length=255)
    user_email: str = Field(min_length=5, max_length=255, index=True)
    user_name: Optional[str] = Field(default=None, max_length=255)
    is_vip: bool = Field(default=False)
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    def __repr__(self):
        return f"<Registration(id='{self.registration_id}', email='{self.user_email}')>"