"""Фабрика FastAPI-приложения"""

# FastAPI
from fastapi import FastAPI

# Зависимости
from bootstrap.lifespan import app_lifespan


def create_app() -> FastAPI:
    """Создает и конфигурирует приложение"""
    app = FastAPI(
        title="Event Bridge Event API", version="1.0.0", lifespan=app_lifespan
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "OK", "message": "Event Bridge Event API is running"}

    return app
