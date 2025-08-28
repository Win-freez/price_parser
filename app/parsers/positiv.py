import asyncio
from pprint import pprint

import httpx
from collections import defaultdict

from schemas.positiv import Category


class PositiveParser:
    BASE_URL = "https://api.positive.ooo/api/v1"

    def __init__(self, limit: int = 30, max_concurrent: int = 10):
        self.limit = limit
        self.semaphore = asyncio.Semaphore(max_concurrent)  # ограничение параллельности

    async def fetch(self, client: httpx.AsyncClient, url: str, params: dict | None = None) -> dict:
        """Асинхронный запрос с ограничением по семафору"""
        async with self.semaphore:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    async def get_categories(self, client: httpx.AsyncClient) -> list[dict]:
        """Забрать все категории"""
        return await self.fetch(client, f"{self.BASE_URL}/category")

    @staticmethod
    def build_category_tree(categories: list[dict]) -> dict:
        """Построить дерево категорий"""
        tree = defaultdict(list)
        for cat in categories:
            parent = cat.get("parent_id")
            tree[parent].append(cat)
        return tree

    def get_leaf_categories(self, tree: dict, parent_id=None) -> list[dict]:
        """Рекурсивно достать конечные категории"""
        leaves = []
        for cat in tree.get(parent_id, []):
            children = self.get_leaf_categories(tree, cat["public_id"])
            if children:
                leaves.extend(children)
            else:
                leaves.append(cat)
        return leaves

    async def fetch_products(self, client: httpx.AsyncClient, category_id: str) -> list[dict]:
        """Забрать все товары в категории"""
        products = []
        page = 1
        while True:
            data = await self.fetch(
                client,
                f"{self.BASE_URL}/product/get-by-category/{category_id}",
                params={"limit": self.limit, "page": page, "sort": "cheap"},
            )
            if not data:
                break
            products.extend(data)
            page += 1
        return products

    async def fetch_product_details(self, client: httpx.AsyncClient, product_id: str) -> dict:
        """Забрать полные данные по товару"""
        return await self.fetch(client, f"{self.BASE_URL}/product/{product_id}")

    @staticmethod
    def _make_categories_tree(categories_list: list[Category]):
        categories_dict = {c.public_id: c for c in categories_list}
        for c in categories_list:
            if c.parent_id:
                categories_dict[c.parent_id].children.append(c)
        return {k: v for k, v in categories_dict.items() if not v.children}


p = PositiveParser()


async def main():
    async with httpx.AsyncClient() as client:
        c = await p.get_categories(client)
        pprint(c)


asyncio.run(main())
