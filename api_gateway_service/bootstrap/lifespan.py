"""Файл отвечает за жизненный цикл приложения (за события startup/shutdown)"""

# Асинхронность
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI

from services.rabbitmq import rabbitmq


@asynccontextmanager
async def app_lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Запускает и останавливает жизненный цикл всего приложения"""

    await asyncio.to_thread(rabbitmq.connect)

    # startup
    yield
    # shutdown

    await asyncio.to_thread(rabbitmq.close)
