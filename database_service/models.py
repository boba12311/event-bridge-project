"""
Pydantic-модели для валидации входящих данных из RabbitMQ.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class RegistrationPayload(BaseModel):
    """Модель для валидации сообщения о регистрации."""
    
    registration_id: str = Field(..., min_length=1, max_length=100)
    event_name: str = Field(..., min_length=1, max_length=255)
    user_email: str = Field(..., min_length=5, max_length=255)
    user_name: Optional[str] = Field(default=None, max_length=255)
    is_vip: bool = Field(default=False)
    timestamp: Optional[datetime] = Field(default=None)
    
    # Игнорируем лишние поля из сообщения
    model_config = ConfigDict(extra='ignore')