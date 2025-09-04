from pydantic import BaseModel


class BrandMention(BaseModel):
    brand_name: str
    mention_count: int
