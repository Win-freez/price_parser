import asyncio

from playwright.async_api import expect, Locator, Page, Browser

from app.parsers.parser import Parser


class EtmParser(Parser):
    BASE_URL = r"https://www.etm.ru"
    SHOP_NAME = "ЭТМ"

    def __init__(self, browser: Browser, word: str, delay: float = 0.5):
        super().__init__(word=word, delay=delay)
        self._browser = browser

    async def search_products(self):
        page = await self.get_page(browser=self._browser, url=self.BASE_URL)

        # Вводим данные в поисковую строку и нажимаем "Enter"
        await self._perform_search(page)
        # Устанавливаем горизонтальное отображение товаров и включаем сортировку "По наличию"
        await page.get_by_test_id("FormatListBulletedIcon").click()
        await self._select_sort_option(page, option_text='По наличию')

        # дожидаемся загрузки страницы
        await page.locator('#nprogress').wait_for(state='hidden')

        # Пролистываем вниз страницы
        await self._scroll_step_by_step(page=page)

        await page.wait_for_load_state("networkidle")

        rows = page.locator('tr[data-testid^="cart-row_wrapper-"]')
        await expect(rows.first).to_be_visible()

        count = await rows.count()
        products = []
        for i in range(count):
            product = rows.nth(i)
            products.append(await self._parse_product(product))
        return products


    async def _perform_search(self, page: Page) -> None:
        input_field = page.get_by_test_id("input-search")
        await expect(input_field).to_be_editable()
        await input_field.click()
        await input_field.type(self.word, delay=20)
        await input_field.press("Enter")

    async def _parse_product(self, product: Locator) -> dict[str, str | float | None]:
        name_locator = product.get_by_test_id("link-good-name")
        name = await name_locator.text_content() if await name_locator.count() > 0 else None

        price_locator = product.locator('td[data-testid="cart-row-7"] p')
        raw_price = await price_locator.text_content() if await price_locator.count() > 0 else None
        price = self._clear_price(raw_price)

        href = await name_locator.get_attribute("href") if await name_locator.count() > 0 else None

        return {
            "shop_name": self.SHOP_NAME,
            "name": name,
            "price": price,
            "url": self.BASE_URL + href if href else None
        }

    @staticmethod
    async def _select_sort_option(page: Page, option_text="По наличию"):
        await page.get_by_test_id("catalog-sort-desktop").click()
        option = page.locator(f'//span[text()="{option_text}"]')
        await option.wait_for(state="visible")
        await option.click()


async def a():
    async with Parser.get_browser() as browser:
        e = EtmParser(browser, "розетка белая")
        return await e.search_products()


print(asyncio.run(a()))