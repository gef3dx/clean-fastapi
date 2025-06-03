import uuid
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy_utils import UUIDType
from src.settings import settings
# from users.settings import settings

__all__ = (
    'Base',
    'Session',
    'AsyncSession',
    'get_async_session',
)

POSTGRES_INDEXES_NAMING_CONVENTION = {
    'ix': '%(column_0_label)s_idx',
    'uq': '%(table_name)s_%(column_0_name)s_key',
    'ck': '%(table_name)s_%(constraint_name)s_check',
    'fk': '%(table_name)s_%(column_0_name)s_fkey',
    'pk': '%(table_name)s_pkey',
}

metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

def create_db_engine():
    if settings.db.provider == 'sqlite+aiosqlite':
        # Для SQLite используем aiosqlite
        return create_async_engine(
            f"sqlite+aiosqlite:///{settings.db.name}",  # Используем name как путь к файлу SQLite
            echo=settings.debug,
            connect_args={"check_same_thread": False}  # Необходимо для async SQLite
        )
    elif settings.db.provider == 'postgresql+asyncpg':
        # Для PostgreSQL (оригинальная конфигурация)
        return create_async_engine(
            settings.db.dsn,
            connect_args={'options': f'-csearch_path={settings.db.scheme}'},
            echo=settings.debug
        )
    else:
        raise ValueError("Неподдерживаемый провайдер базы данных")

asyncio_engine = create_db_engine()

AsyncSessionFactory = async_sessionmaker(
    asyncio_engine,
    autocommit=False,
    expire_on_commit=False,
    future=True,
    autoflush=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    metadata = metadata

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(binary=False),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid() if settings.db.provider != 'sqlite+aiosqlite' else None
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session


Session = Annotated[AsyncSession, Depends(get_async_session)]