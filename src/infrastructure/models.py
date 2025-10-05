from typing import Optional
from pydantic import BaseModel
from sqlmodel import JSON, Field, SQLModel


class SentimentBody(BaseModel):
    brand: str
    brand_model: str
    positive_phrases: list[str] = Field(sa_type=JSON)
    negative_phrases: list[str] = Field(sa_type=JSON)


class Sentiments(SQLModel, table=True):
    id: int = Field(primary_key=True, default=None)
    brand_report_id: str
    date: str
    model: str
    brand: str
    brand_model: Optional[str]
    positive_phrases: list[str] = Field(sa_type=JSON)
    negative_phrases: list[str] = Field(sa_type=JSON)


class Citations(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    brand_report_id: str
    date: str
    model: str
    brand: str
    rank: Optional[int]
    title: Optional[str]
    domain: Optional[str]
    norm_url: Optional[str]


class Output_Reports(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    brand_report_id: str
    date: str
    model: str
    snapshot: str
    markdown: str


class Brand_Metrics(BaseModel):
    brand: str
    mention_count: int
    position: int
