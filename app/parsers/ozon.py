import asyncio

from playwright.async_api import Page

from app.parsers.parser import Parser


class OzonParser(Parser):
    BASE_URL = r"https://www.ozon.ru/"

    def __init__(
            self,
            word: str,
            delay: float = 0.3,
    ):
        self.word = word
        self._delay = delay


    async def search_products(self):
        async with self.get_browser() as browser:
            page = await self.get_page(
                browser=browser,
                url=self.BASE_URL,
            )

            search_input = page.get_by_placeholder("Искать на Ozon")
            await search_input.wait_for(state="visible")

            await search_input.fill(self.word)
            await search_input.press("Enter", delay=self._delay)

            await page.wait_for_load_state(state="networkidle")

            await self._scroll_step_by_step(page, max_scrolls=2)

            products = page.locator("div.tile-root")
            count = await products.count()

            filtered_products = []

            for i in range(count):
                product = products.nth(i)
                name = await product.locator("span.tsBody500Medium").inner_text()
                price = await product.locator("span.tsHeadline500Medium").inner_text()
                href = await product.locator("a.tile-clickable-element.ir0_24").get_attribute("href")
                full_link = f"https://www.ozon.ru{href}"

                filtered_products.append({
                    "name": name,
                    "price": price,
                    "link": full_link
                })

            return filtered_products

parser = OzonParser("люстра")
html = asyncio.run(parser.search_products())
print(html)
