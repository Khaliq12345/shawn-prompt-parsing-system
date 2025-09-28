from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import DateTime, Integer, Text


class Base(DeclarativeBase):
    pass


class BrandModel(BaseModel):
    brand_name: str
    mention_count: int
    position: int


# Brand Mention Model
class BrandDB(AsyncAttrs, Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")
    process_id: Mapped[str] = mapped_column(Text())
    prompt_id: Mapped[str] = mapped_column(Text())
    brand_name: Mapped[str] = mapped_column(Text())
    mention_count: Mapped[int] = mapped_column(Integer())
    position: Mapped[int] = mapped_column(Integer())
    date: Mapped[datetime] = mapped_column(DateTime())


# Brand Mention Model
class LlmProcess(AsyncAttrs, Base):
    __tablename__ = "llmprocess"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")
    process_id: Mapped[str] = mapped_column(Text())
    prompt_id: Mapped[str] = mapped_column(Text())
    status: Mapped[str] = mapped_column(Text())
    date: Mapped[datetime] = mapped_column(DateTime())
