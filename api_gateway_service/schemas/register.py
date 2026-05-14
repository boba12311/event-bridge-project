"""Схемы для регистрации"""

from pydantic import BaseModel, Field
# from pydantic import EmailStr # <-- Расскомментировать, если решите использовать


class RegisterUserRequest(BaseModel):
    """Схема запроса к API"""

    event_name: str = Field(..., min_length=2, max_length=100)
    user_email: str = Field(...)
    # user_email: EmailStr = Field(..., max_length=255) # <-- Будет автоматическая валидация на соответствие международному стандарту: название_почты@регистратор.домен
    user_name: str = Field(..., min_length=2, max_length=100)
    is_vip: bool = False


class RegisterUserResponseSuccess(BaseModel):
    """Схема ответа, в случае удачи"""

    status: str = "success"
    message: str = "Ваша заявка принята в обработку"
    registration_id: str = Field(..., description="Уникальный идентификатор")


class RegisterUserResponseFail(BaseModel):
    """Схема ответа, в случае неудачи"""

    status: str = "fail"
    message: str = "Что-то пошло не так, попробуйте еще раз"
