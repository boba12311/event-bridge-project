"""
Утилиты для работы с базой данных.
"""

import logging
from sqlmodel import Session, select, SQLModel, create_engine

from core.config import DATABASE_URL
from db.schemas import Registration

logger = logging.getLogger(__name__)

# Создаём engine один раз при импорте модуля
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)


def init_db():
    """Создаёт таблицы, если их ещё нет."""
    SQLModel.metadata.create_all(engine)
    logger.info("✅ Таблица '%s' готова", Registration.__tablename__)


def save_registration(data: dict) -> bool:
    """
    Сохраняет регистрацию в базу данных.
    
    Args:
        data: Словарь с данными регистрации
        
    Returns:
        bool: True если успешно, False если ошибка
    """
    try:
        with Session(engine) as session:
            # Проверяем на дубликат
            statement = select(Registration).where(
                Registration.registration_id == data["registration_id"]
            )
            existing = session.exec(statement).first()
            
            if existing:
                logger.warning(f"Дубликат: {data['registration_id']} — пропускаем")
                return True
            
            # Создаём новую запись
            registration = Registration(**data)
            session.add(registration)
            session.commit()
            session.refresh(registration)
            
            logger.info(f"Сохранено: {registration.registration_id} ({registration.user_email})")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        return False


def get_registration_by_id(registration_id: str) -> Registration | None:
    """Ищет регистрацию по ID."""
    with Session(engine) as session:
        statement = select(Registration).where(
            Registration.registration_id == registration_id
        )
        return session.exec(statement).first()