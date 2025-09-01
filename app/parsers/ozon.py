import asyncio
from pprint import pprint

from playwright.async_api import Page, expect, Locator, Browser

from app.parsers.parser import Parser


class OzonParser(Parser):
    BASE_URL = r"https://www.ozon.ru"
    SHOP_NAME = "Озон"

    def __init__(self, browser: Browser, word: str, delay: float = 0.5):
        super().__init__(word=word, delay=delay)
        self._browser = browser

    async def _perform_search(self, page: Page) -> None:
        search_input = page.locator('input[placeholder="Искать на Ozon"]')
        await expect(search_input).to_be_editable()
        await search_input.fill(self.word)
        await search_input.press("Enter")

    async def _parse_product(self, product: Locator):
        name_locator = product.locator("span.tsBody500Medium")
        name = await name_locator.text_content() if await name_locator.count() > 0 else None

        price_locator = product.locator("span.tsHeadline500Medium")
        price_raw = await price_locator.text_content() if await price_locator.count() > 0 else "0"

        href_locator = product.locator("a[href*='/product/']")
        href = await href_locator.first.get_attribute("href") if await href_locator.count() > 0 else None

        price = float(self._clear_price(price_raw))

        return {
            "shop_name": self.SHOP_NAME,
            "name": name,
            "price": price,
            "url": self.BASE_URL + href if href else None,
        }

    async def search_products(self):
        page = await self.get_page(browser=self._browser, url=self.BASE_URL)
        await self._perform_search(page=page)

        await page.wait_for_selector("div.tile-root")
        await self._scroll_step_by_step(page, max_scrolls=4)

        products = page.locator("div.tile-root")
        count = await products.count()
        results = []

        for i in range(count):
            product = products.nth(i)
            results.append(await self._parse_product(product))

        return results
