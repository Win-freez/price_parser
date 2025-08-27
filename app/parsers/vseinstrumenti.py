import asyncio
from pprint import pprint

from playwright.async_api import Page, expect, Locator, Browser

from app.parsers.parser import Parser


class VseinstrumentiParser(Parser):
    BASE_URL = r"https://www.vseinstrumenti.ru/"
    SHOP_NAME = "Все инструменты"

    def __init__(self, browser: Browser, word: str, delay: float = 0.5):
        super().__init__(word=word, delay=delay)
        self._browser = browser

    async def _perform_search(self, page: Page) -> None:
        # Заполняет данные в поисковой строке и нажимает на кнопку поиска
        input_field = page.locator('[data-qa="header-search-input"]')
        await expect(input_field).to_be_editable()
        await input_field.click()
        await asyncio.sleep(self._delay)
        await input_field.type(self.word, delay=40)
        btn = page.locator('[data-qa="header-search-button"]')
        await btn.click()

    async def _parse_product(self, product: Locator) -> dict[str, str | float | None]:
        # Проходит по странице с продуктами и собирает информацию (название, цена, ссылка)
        name = await product.locator('[data-qa="product-name"]').inner_text()
        price_raw = await product.locator('[data-qa="product-price-current"]').text_content()
        href = await product.locator('[data-qa="product-name"]').get_attribute("href")
        price = self._clear_price(price_raw)
        return {
            "shop_name": self.SHOP_NAME,
            "name": name.strip() if name else None,
            "price": int(price) if price else None,
            "url": href or None,
        }

    async def search_products(self) -> list[dict[str, str | int | None]]:
        page = await self.get_page(browser=self._browser, url=self.BASE_URL)
        await self._perform_search(page)

        await expect(page.locator('[data-qa="listing"]')).to_be_visible()
        products = page.locator('[data-qa="products-tile"]')
        count = await products.count()

        results = []
        for i in range(count):
            product = products.nth(i)
            results.append(await self._parse_product(product))

        return results
