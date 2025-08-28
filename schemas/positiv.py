from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, HttpUrl, Field


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')


class BalanceInfo(BaseModel):
    count: str
    unit: str
    residual: str


class AmountInfo(BaseModel):
    value: str
    currency: str


class Info1C(BaseModel):
    product_id: str
    row_id: str
    store_id: str
    name: str
    balance: BalanceInfo
    amount: AmountInfo
    vendorCode: str
    code: str
    links: str


class StoreInfo1C(BaseModel):
    name: str
    storeId: str


class Store(BaseModel):
    id: str
    public_id: str
    storeId: str
    name: str
    info_1c: StoreInfo1C
    createdAt: datetime
    updatedAt: datetime


class Attribute(BaseModel):
    filterId: str
    valueId: str
    value: str
    name: str
    priority: int
    description: str
    isSearchFilter: bool
    isRange: bool
    step: int


class Product(BaseConfigModel):
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
    info_1c: Info1C
    unpublishedDate: datetime | None
    createdAt: datetime
    nameVector: str
    updatedAt: datetime
    store: Store
    category: Category
    attributes: list[Attribute]


class Category(BaseConfigModel):
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
    children: list["Category"] = Field(default_factory=list)
    products: list["Product"] = Field(default_factory=list)
