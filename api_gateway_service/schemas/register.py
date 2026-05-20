"""Схемы для регистрации"""

from pydantic import BaseModel, EmailStr, Field


# =========================
# == Схема запроса к API ==
class RegisterUserRequest(BaseModel):
    """Схема запроса к API"""

    event_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Название события",
        json_schema_extra={"example": "Python Conference"},
    )

    user_email: EmailStr = Field(
        ...,
        max_length=255,
        description="Email пользователя (валидируется на соответствие международному стандарту)",
        json_schema_extra={"example": "ivan@example.com"},
    )
    user_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Имя и фамилия пользователя",
        json_schema_extra={"example": "Иван Иванов"},
    )

    is_vip: bool = Field(
        default=False,
        description="Флаг VIP-статуса пользователя (ВАЖНО: влияет на маршрутизацию)",
        json_schema_extra={"example": True},
    )

    body: dict = Field(
        description="Простое сообщение (необязательно)",
        json_schema_extra={"example": "События о Python!"},
    )


# =========================
# == Схема ответа от API ==


class RegisterUserResponseSuccess(BaseModel):
    """Схема ответа, в случае удачи"""

    status: str = Field(default="success", description="Статус ответа")
    message: str = Field(
        default="Ваша заявка принята в обработку",
        description="Сообщение о результате регистрации",
    )
    registration_id: str = Field(
        ...,
        description="Уникальный идентификатор регистрации (генерируется автоматически uuid4)",
    )


class RegisterUserResponseFail(BaseModel):
    """Схема ответа, в случае неудачи"""

    status: str = Field(default="fail", description="Статус ответа")
    message: str = Field(
        default="Что-то пошло не так, попробуйте еще раз",
        description="Сообщение об ошибке",
    )
