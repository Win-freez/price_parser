import asyncio
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Page, Browser


class Parser:
    @classmethod
    @asynccontextmanager
    async def get_browser(cls):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized"
                ]
            )
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/115.0.0.0 Safari/537.36"
            )
            try:
                yield context
            finally:
                await browser.close()

    @classmethod
    async def get_page(cls, browser: Browser, url: str, timeout: int = 30000) -> Page:
        page: Page = await browser.new_page()
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            """
        )
        await page.goto(url, timeout=timeout)
        return page


    @staticmethod
    async def _scroll_step_by_step(page, step: int = 500, delay: float = 1.0, max_scrolls: int = 30) -> None:
        """
        Прокручивает страницу вниз по шагам (например, 500px за раз).

        :param page: Playwright page объект
        :param step: количество пикселей за один скролл
        :param delay: задержка между скроллами (сек)
        :param max_scrolls: максимальное количество шагов
        """
        for _ in range(max_scrolls):
            await page.evaluate(f"window.scrollBy(0, {step});")
            await asyncio.sleep(delay)