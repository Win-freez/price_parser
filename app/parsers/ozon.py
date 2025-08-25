import asyncio
import re
from logging import captureWarnings
from pprint import pprint

from playwright.async_api import Page, expect, Locator

from app.parsers.parser import Parser


class OzonParser(Parser):
    BASE_URL = r"https://www.ozon.ru/"

    def __init__(
            self,
            word: str,
            delay: float = 0.2,
    ):
        self.word = word
        self._delay = delay


    async def _perform_search(self, page: Page) -> None:
        search_input = page.locator("div[data-widget='searchBarDesktop'] input")
        await search_input.wait_for(state="visible")

        await search_input.fill(self.word)
        await search_input.press("Enter", delay=self._delay)


    async def _parse_product(self, product: Locator):
        name = await product.locator("span.tsBody500Medium").text_content()
        price_raw = await product.locator("span.tsHeadline500Medium").text_content()
        href = await product.locator("a.tile-clickable-element.ir0_24").get_attribute("href")

        price = int(self._clear_price(price_raw))
        return {
            "name" : name,
            "price": price,
            "url": f"https://www.ozon.ru{href}" if href else None
        }



    async def search_products(self):
        async with self.get_browser() as browser:
            page = await self.get_page(browser=browser, url=self.BASE_URL)
            await self._perform_search(page=page)

            await expect(page.locator("#contentScrollPaginator")).to_be_visible()
            await self._scroll_step_by_step(page, max_scrolls=2)

            products = page.locator("div.tile-root")
            count = await products.count()
            results = []

            for i in range(count):
                product = products.nth(i)
                results.append(await self._parse_product(product))

            return results

