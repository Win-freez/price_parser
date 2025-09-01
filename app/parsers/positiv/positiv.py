import asyncio
import logging
from asyncio import create_task, gather
from typing import Any, AsyncGenerator, cast

from httpx import AsyncClient, TimeoutException, HTTPError
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, after_log

from app.logging_config import setup_logging
from app.schemas.positiv.category import CategorySchema
from app.schemas.positiv.product import ProductCategorySchema, ProductSchema

setup_logging()
logger = logging.getLogger(__name__)


class PositiveParserAPI:
    BASE_URL = "https://api.positive.ooo/api/v1"

    def __init__(
            self,
            client: AsyncClient,
            max_concurrent: int = 10
    ) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.client = client

    @retry(
        stop=stop_after_attempt(3),
        reraise=True,
        after=after_log(logger, logging.WARNING)
           )
    async def fetch(
            self,
            url: str,
            params: dict | None = None,
            delay: float = 0
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Асинхронный запрос с ограничением по семафору и логированием"""
        async with self.semaphore:
            try:
                r = await self.client.get(url, params=params, timeout=15)
                r.raise_for_status()
                await asyncio.sleep(delay)
                return r.json()
            except TimeoutException:
                logger.error(f"Timeout при запросе {url}")
                raise
            except HTTPError as e:
                logger.error(f"Ошибка HTTP {e} при запросе {url}")
                raise
            except Exception as e:
                logger.exception(f"Неожиданная ошибка при запросе {url}: {e}")


    async def get_categories(
            self,
    ) -> dict[str, CategorySchema]:
        """Забрать все категории"""
        logger.info("Получение информации о всех категориях")
        categories = await self.fetch(f"{self.BASE_URL}/category")
        categories_dict = {}
        for raw in categories:
            try:
                category = CategorySchema(**raw)
                categories_dict[category.public_id] = category
            except ValidationError as e:
                logger.error("Ошибка валидации категории: %s", e)
        return categories_dict


    async def fetch_product_full_info(
            self,
            product_id: str
    ) -> ProductSchema | None:
        """Забрать полные данные по товару"""
        logger.info("Получение всех данных о товаре c product_id: %s", product_id)
        product = await self.fetch(f"{self.BASE_URL}/product/{product_id}")
        if not product:
            logger.error(
                "Ошибка данных для product_id=%s: %s",
                product_id,
            )
            return None

        return self._safe_validate(ProductSchema, product, context=product_id)



    async def fetch_products_by_category(
            self,
            public_id: str
    ) -> list[ProductCategorySchema]:
        logger.info(
            "Получение всех продуктов из категории с public_id: %s",
            public_id
        )
        products = await self.fetch(
            f"{self.BASE_URL}/product/get-by-category/{public_id}"
        )
        if not products:
            logger.warning(
                "Не удалось получить продукты для категории %s",
                public_id
            )
            return []

        result = [
            self._safe_validate(ProductCategorySchema, product, context=public_id)
            for product in products
        ]
        return result


    async def walk_categories(
            self,
            category: CategorySchema,
            depth: int = 0
    ) -> AsyncGenerator[tuple[int, str, list[ProductSchema]]]:
        """Асинхронно обходит категорию и её подкатегории, собирает товары"""
        logger.debug(
            "Обрабатываю категорию '%s' на глубине %s",
            category.name, depth
        )
        if category.children:
            logger.info(
                "Категория '%s' (глубина %s) содержит %s подкатегорий",
                category.name, depth, len(category.children)
            )
            yield depth, category.name, []

            for inner_category in category.children:
                async for node in self.walk_categories(category=inner_category, depth=depth + 1):
                    yield node

        else:
            products_short_info = await self.fetch_products_by_category(public_id=category.public_id)
            tasks = self._create_tasks_for_products(products_short_info)
            products = await gather(*tasks, return_exceptions=True)
            filtered_products = []
            for p in products:
                if isinstance(p, Exception):
                    logger.exception("Ошибка при обработке товара", exc_info=p)
                elif p is not None:
                    filtered_products.append(p)

            logger.info(
                "В категории '%s' (глубина %s) получено %s товаров (ошибок: %s)",
                category.name, depth, len(filtered_products), len(products) - len(filtered_products)
            )

            yield depth, category.name, cast(list[ProductSchema],filtered_products)

    @staticmethod
    def make_categories_with_children(
            categories_dict: dict[str, CategorySchema]
    ) -> dict[str, CategorySchema]:

        for public_id, category in categories_dict.items():
            if category.parent_id:
                parent = categories_dict.get(category.parent_id)
                if parent:
                    parent.children.append(category)
                else:
                    logger.warning(
                        "Не найден родитель с public_id=%s для категории %s",
                        category.parent_id, category.name
                    )
        return categories_dict

    def _create_tasks_for_categories(self, categories: dict[str, CategorySchema]) -> list[asyncio.Task]:
        """Создать задачи для получения продуктов по категориям"""
        tasks = []
        for category in categories.values():
            task = create_task(
                self.fetch_products_by_category(category.public_id),
                name=category.name
            )
            tasks.append(task)
        return tasks

    def _create_tasks_for_products(self, products: list[ProductCategorySchema]) -> list[asyncio.Task]:
        tasks = []
        for product in products:
            task = create_task(
                self.fetch_product_full_info(product.public_id),
                name=product.name
            )
            tasks.append(task)
        return tasks

    @staticmethod
    def _safe_validate(schema, data, context=""):
        try:
            return schema(**data)
        except ValidationError as e:
            logger.error("Ошибка валидации %s: %s", context, e)
        except TypeError as e:
            logger.error("Ошибка данных %s: %s", context, e)
        return None

