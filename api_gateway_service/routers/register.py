"""Роуты для регистрации"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone
import uuid

from schemas.register import (
    RegisterUserRequest,
    RegisterUserResponseSuccess,
)
from services.rabbitmq import rabbitmq

router = APIRouter(tags=["registration"])


@router.post(
    "/register",
    summary="Регистрация нового пользователя",
    description="Регистрирует нового пользователя",
    response_model=RegisterUserResponseSuccess,
    status_code=status.HTTP_202_ACCEPTED,
)
async def register(request: RegisterUserRequest):
    # 1. Генерируем ID
    registration_id = str(uuid.uuid4())
    registration_time = datetime.now(timezone.utc).isoformat()

    # 2. Формируем событие для RabbitMQ
    event_message = {
        "registration_id": registration_id,
        "registration_time": registration_time,
        "event_name": request.event_name,
        "user_email": request.user_email,
        "user_name": request.user_name,
        "is_vip": request.is_vip,
    }

    # 3. Определяем routing key
    routing_key = (
        "event.registered.vip" if request.is_vip else "event.registered.regular"
    )

    # 4. Публикуем в RabbitMQ
    try:
        rabbitmq.publish(routing_key, event_message)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис временно недоступен. Попробуйте позже.",
        )

    # 5. Возвращаем успех
    return RegisterUserResponseSuccess(registration_id=registration_id)
