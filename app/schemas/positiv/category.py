from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field


class CategorySchema(BaseModel):
    id: str
    public_id: str
    name: str
    slug: str
    imageUrl: HttpUrl | None
    iconUrl: HttpUrl | None
    parent_id: str | None
    isPublished: bool
    priority: int
    publishedDate: datetime
    unpublishedDate: datetime | None
    createdAt: datetime | None
    updatedAt: datetime | None
    children: list["CategorySchema"] = Field(default_factory=list)


CategorySchema.model_rebuild()
