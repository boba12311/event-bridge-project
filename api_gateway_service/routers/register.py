"""Роуты для регистрации"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from schemas.register import (
    RegisterUserRequest,
    RegisterUserResponseSuccess,
)
from services.rabbitmq import rabbitmq

router = APIRouter(tags=["registration"])


@router.post(
    "/register",
    summary="Регистрация участника мероприятия",
    description=(
        """
Принимает JSON с данными пользователя, валидирует email и структуру.

Генерирует `UUID` регистрации, фиксирует timestamp и публикует событие в `RabbitMQ`.

При `is_vip=true` сообщение уходит в `event.registered.vip`, иначе в `event.registered.regular`.
        """
    ),
    response_description="ID созданной регистрации и статус принятия в обработку",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        422: {
            "description": "Ошибка валидации полей (невалидный email или отсутствие обязательных полей)"
        },
        503: {"description": "RabbitMQ недоступен, событие не опубликовано"},
    },
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
        "body": request.body,
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
            detail="Сервис временно недоступен. Попробуйте позже",
        )

    # 5. Возвращаем успех
    return RegisterUserResponseSuccess(registration_id=registration_id)
