"""Файл отвечает за жизненный цикл приложения (за события startup/shutdown)"""

# Асинхронность
import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from services.rabbitmq import rabbitmq


@asynccontextmanager
async def app_lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Запускает и останавливает жизненный цикл всего приложения"""

    await asyncio.to_thread(rabbitmq.connect_with_retry)

    # startup
    yield
    # shutdown

    await asyncio.to_thread(rabbitmq.close)
