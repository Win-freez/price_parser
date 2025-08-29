import asyncio
import logging
from asyncio import create_task
from typing import Any, AsyncGenerator, cast

import httpx
from httpx import AsyncClient, TimeoutException, HTTPError

from app.schemas.positiv.category import CategorySchema
from app.schemas.positiv.product import ProductCategorySchema, ProductSchema

logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d"
           " %(levelname)-7s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class PositiveParserAPI:
    BASE_URL = "https://api.positive.ooo/api/v1"

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
            delay: float = 0
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Асинхронный запрос с ограничением по семафору и логированием"""
        async with self.semaphore:
            try:
                r = await self.client.get(url, params=params, timeout=15.0)
                r.raise_for_status()
                await asyncio.sleep(delay)
                return r.json()
            except TimeoutException:
                logger.error(f"Timeout при запросе {url}")
            except HTTPError as e:
                logger.error(f"Ошибка HTTP {e} при запросе {url}")
            except Exception as e:
                logger.exception(f"Неожиданная ошибка при запросе {url}: {e}")

    async def get_categories(
            self,
    ) -> dict[str, CategorySchema]:
        """Забрать все категории"""
        logger.info("Получение информации о всех категориях")
        categories = await self.fetch(f"{self.BASE_URL}/category")
        categories_gen = (CategorySchema(**category) for category in categories)
        categories_dict = {category.public_id: category for category in categories_gen}
        return categories_dict

    async def fetch_product_full_info(
            self,
            product_id: str
    ) -> ProductSchema:
        """Забрать полные данные по товару"""
        logger.info("Получение всех данных о товаре c product_id: %s", product_id)
        product = await self.fetch(f"{self.BASE_URL}/product/{product_id}")
        return ProductSchema(**product)

    async def fetch_products_by_category(
            self,
            public_id: str
    ) -> dict[str, list[ProductCategorySchema]]:
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
            return {}

        return {public_id: [ProductCategorySchema(**product) for product in products]}

    async def get_all_products_short_info(self) -> AsyncGenerator[tuple[str, list[ProductCategorySchema]]]:
        all_categories = await self.get_categories()
        categories_without_children = self._make_categories_without_children(all_categories)
        tasks = self._create_tasks_for_categories(categories_without_children)
        for task in asyncio.as_completed(tasks):
            try:
                products_dict = await task
                if not products_dict:
                    logger.warning("Отсутсвует товар")
                else:
                    for public_id, products in products_dict.items():
                        category_name = all_categories[public_id].name
                        logger.info(
                            "Получены значения по категории: %s, кол-во продуктов: %s",
                            category_name,
                            len(products)
                        )
                        yield category_name, products

            except (httpx.RequestError, httpx.HTTPStatusError):
                logger.exception("Ошибка в запросе HTTP")
            except asyncio.TimeoutError:
                logger.exception("Вышло время")
            except KeyError:
                logger.exception("Не найдено значение по ключу")
            except Exception:
                logger.exception("Непридведенная ошибка")

    async def get_all_products_full_info(self) -> AsyncGenerator[tuple[str, list[ProductSchema]], None]:
        async for category, products in self.get_all_products_short_info():
            tasks = self._create_tasks_for_products(products)
            full_products = await asyncio.gather(*tasks, return_exceptions=True)

            full_products_clean = []
            for product in full_products:
                if isinstance(product, Exception):
                    logger.exception(
                        f"Ошибка при получении полного товара: %s",
                        product
                    )
                else:
                    full_products_clean.append(cast(ProductSchema, product))
                    logger.info("Данные по товару: %s успешно получены", product)

            yield category, full_products_clean

    @staticmethod
    def _make_categories_without_children(
            categories_dict: dict[str, CategorySchema]
    ) -> dict[str, CategorySchema]:
        for public_id, category in categories_dict.items():
            if category.parent_id:
                categories_dict[category.parent_id].children.append(category)
        return {
            category.name: category
            for public_id, category in categories_dict.items()
            if not category.children
        }

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
