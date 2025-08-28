from __future__ import annotations

from datetime import datetime
from typing import List, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, HttpUrl

if TYPE_CHECKING:
    from app.schemas.positiv.category import CategorySchema


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')


class BalanceInfoSchema(BaseModel):
    count: str
    unit: str
    residual: str


class AmountInfoSchema(BaseModel):
    value: str
    currency: str


class Info1CSchema(BaseModel):
    product_id: str
    row_id: str
    store_id: str
    name: str
    balance: BalanceInfoSchema
    amount: AmountInfoSchema
    vendorCode: str
    code: str
    links: str


class StoreInfo1CSchema(BaseModel):
    name: str
    storeId: str


class StoreSchema(BaseModel):
    id: str
    public_id: str
    storeId: str
    name: str
    info_1c: StoreInfo1CSchema
    createdAt: datetime
    updatedAt: datetime


class AttributeSchema(BaseModel):
    filterId: str
    valueId: str
    value: str
    name: str
    priority: int
    description: str
    isSearchFilter: bool
    isRange: bool
    step: int


class ProductSchema(BaseConfigModel):
    public_id: str
    name: str
    slug: str
    imageUrl: HttpUrl | None
    vendorCode: str
    code: str
    description: str
    snippet: str
    monthWarranty: str | None
    count: int
    unitOfMeasurement: str
    isAvailable: bool
    stockStatus: str
    images: List[HttpUrl]
    price: str
    currency: str
    isNew: bool
    isPopular: bool
    isSeasonal: bool
    isGift: bool
    links1c: str
    isPublished: bool
    publishedDate: datetime
    info_1c: Info1CSchema
    unpublishedDate: datetime | None
    createdAt: datetime
    nameVector: str
    updatedAt: datetime
    store: StoreSchema
    category: CategorySchema
    attributes: list[AttributeSchema]


class ProductCategorySchema(BaseConfigModel):
    id: str
    public_id: str
    categoryId: str
    code: str
    slug: str
    name: str
    description: str | None = None
    snippet: str | None = None
    imageUrl: HttpUrl | None = None

    price: str
    count: int

    isNew: bool
    isPopular: bool
    isPublished: bool
