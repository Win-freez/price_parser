
from app.parsers.parser import Parser


class RubinParser(Parser):
    BASE_URL = r"https://tdrubin.com/"

    async def find_product_by_article(self, article: str):
        async with self.get_browser() as browser:
            page = await self.get_page(browser=browser, url=self.BASE_URL)
            await page.locator("#title-searchs-input").fill(article)
            await page.keyboard.press("Enter", delay=0.3)
            await page.wait_for_load_state("domcontentloaded")
            products = await page.locator("img[title]").all()

            return products



