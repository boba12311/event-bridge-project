"""Фабрика FastAPI-приложения"""

# FastAPI
from fastapi import FastAPI

# Импорт роутера
from routers.register import router as register_router

# Зависимости
from .lifespan import app_lifespan


def create_app() -> FastAPI:
    """Создает и конфигурирует приложение"""
    app = FastAPI(
        title="Event Bridge Event API", version="1.0.0", lifespan=app_lifespan
    )

    app.include_router(register_router)

    @app.get(
        "/",
        summary="Проверка доступности API",
        description="Проверяет, что сервис доступен и работает",
    )
    async def root() -> dict[str, str]:
        """Возвращает статус "OK" и сообщение о том, что сервис работает"""
        return {"status": "OK", "message": "Event Bridge Event API is running"}

    return app
