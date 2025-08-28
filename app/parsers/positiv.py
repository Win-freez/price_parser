import asyncio
from asyncio import create_task
from pprint import pprint

import httpx
from httpx import AsyncClient

from app.schemas.positiv.category import CategorySchema
from app.schemas.positiv.product import ProductCategorySchema, ProductSchema


class PositiveParserAPI:
    BASE_URL = "https://api.positive.ooo/api/v1"
    URL_PRODUCT_BY_CATEGORY = "https://api.positive.ooo/api/v1/product/get-by-category/"

    def __init__(
            self,
            client: AsyncClient,
            limit: int = 30,
            max_concurrent: int = 10
    ) -> None:
        self.limit = limit
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.client = client

    async def fetch(
            self,
            url: str,
            params: dict | None = None,
            delay: float = 0.1
    ) -> dict:
        """Асинхронный запрос с ограничением по семафору"""
        async with self.semaphore:
            r = await self.client.get(url, params=params)
            r.raise_for_status()
            await asyncio.sleep(delay)
            return r.json()

    async def get_categories(
            self,
    ) -> list[CategorySchema]:
        """Забрать все категории"""
        categories = await self.fetch(f"{self.BASE_URL}/category")
        return [CategorySchema(**category) for category in categories]

    async def fetch_product_full_info(
            self,
            product_id: str
    ) -> ProductSchema:
        """Забрать полные данные по товару"""
        product = await self.fetch(f"{self.BASE_URL}/product/{product_id}")
        return ProductSchema(**product)

    async def fetch_products_by_category(
            self,
            public_id: str
    ) -> list[ProductCategorySchema]:
        products = await self.fetch(
            f"{self.BASE_URL}/product/get-by-category/{public_id}"
        )
        return [ProductCategorySchema(**product) for product in products]

    @staticmethod
    def _make_categories_without_children(
            categories_list: list[CategorySchema]
    ) -> list[CategorySchema]:
        categories_dict = {category.public_id: category for category in categories_list}
        for c in categories_list:
            if c.parent_id:
                categories_dict[c.parent_id].children.append(c)
        return [
            category for public_id, category in categories_dict.items()
            if not category.children
        ]

    async def get_all_products(self):
        all_categories = await self.get_categories()
        categories_without_children = self._make_categories_without_children(all_categories)
        tasks = []
        for category in categories_without_children:
            task = create_task(self.fetch_products_by_category(category.public_id))
            task.set_name(category.name)
            tasks.append(task)

        products_by_categories = await asyncio.gather(*tasks, return_exceptions=True)
        result = {}
        for task, products in zip(tasks, products_by_categories):
            if isinstance(products, Exception):
                result[task.get_name()] = products
            else:
                result[task.get_name()] = products

        return result


async def main():
    async with httpx.AsyncClient() as client:
        p = PositiveParserAPI(client=client)
        products = await p.get_all_products()
        pprint(products)


asyncio.run(main())
