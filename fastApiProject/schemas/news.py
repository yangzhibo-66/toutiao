from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewsItemBase


class NewsCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=10)
    image: Optional[str] = Field(None, max_length=255)
    author: Optional[str] = Field(None, max_length=50)
    category_id: int = Field(..., alias="categoryId")

    model_config = ConfigDict(populate_by_name=True)


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
