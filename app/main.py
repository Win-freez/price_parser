import asyncio

import httpx

from app.logging_config import setup_logging
from app.parsers.positiv.excel_writer import save_products_to_excel
from app.parsers.positiv.positiv import PositiveParserAPI

setup_logging()

async def main():
    async with httpx.AsyncClient() as client:
        parser = PositiveParserAPI(client=client, max_concurrent=100)
        await save_products_to_excel(parser, filename="positiv_products.xlsx")


asyncio.run(main())