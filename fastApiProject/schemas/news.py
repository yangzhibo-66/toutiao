from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase


class RelatedNewsResponse(BaseModel):
    id: int
    title: str
    image: Optional[str] = None
    source_url: Optional[str] = Field(None, alias="sourceUrl")
    views: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NewsDetailResponse(NewsItemBase):
    content: str
    related_news: list[RelatedNewsResponse] = Field(default_factory=list, alias="relatedNews")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
