# message_contract.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

class RegistrationEvent(BaseModel):
    registration_id: str = str(uuid.uuid4())
    event_name: str
    user_email: EmailStr
    user_name: str
    is_vip: bool = False
    registration_time: str = datetime.utcnow().isoformat()

# Пример готового сообщения для тестов
TEST_VIP_EVENT = RegistrationEvent(
    event_name="Python Summit 2026",
    user_email="student@university.ru",
    user_name="Андрей",
    is_vip=True
).model_dump()