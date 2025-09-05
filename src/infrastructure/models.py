from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from src.config import config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs
from sqlalchemy import DateTime, Integer, Text


def get_engine():
    engine = create_async_engine(
        f"postgresql+psycopg://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:5432/{config.DB_NAME}"
    )
    return engine


class Base(DeclarativeBase):
    pass


class BrandMention(BaseModel):
    brand_name: str
    mention_count: int


# Brand Mention Model
class BrandMentionDB(AsyncAttrs, Base):
    __tablename__ = "brandmentions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")
    process_id: Mapped[str] = mapped_column(Text())
    prompt_id: Mapped[str] = mapped_column(Text())
    brand_name: Mapped[str] = mapped_column(Text())
    mention_count: Mapped[float] = mapped_column(Integer())
    date: Mapped[datetime] = mapped_column(DateTime())


# Brand Mention Model
class LlmProcess(AsyncAttrs, Base):
    __tablename__ = "llmprocess"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")
    process_id: Mapped[str] = mapped_column(Text())
    prompt_id: Mapped[str] = mapped_column(Text())
    status: Mapped[str] = mapped_column(Text())
    date: Mapped[datetime] = mapped_column(DateTime())


# Create all tables of the database
async def create_db_and_tables():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
