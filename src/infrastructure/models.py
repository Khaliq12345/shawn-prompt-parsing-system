from typing import Optional
from sqlmodel import JSON, Field, SQLModel


class Sentiments(SQLModel, table=True):
    id: int = Field(primary_key=True)
    brand_report_id: str
    date: str
    model: str
    brand: str
    positive_phrases: list[str] = Field(sa_type=JSON)
    negative_phrase: list[str] = Field(sa_type=JSON)


class Citations(SQLModel, table=True):
    id: int = Field(primary_key=True)
    brand_report_id: str
    date: str
    model: str
    brand: str
    rank: Optional[int]
    title: Optional[str]
    domain: Optional[str]
    norm_url: Optional[str]
