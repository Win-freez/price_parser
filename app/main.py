import asyncio

import httpx

from app.logging_config import setup_logging
from app.parsers.positiv.excel_writer import save_products_to_excel
from app.parsers.positiv.positiv import PositiveParserAPI

setup_logging()

async def main():
    async with httpx.AsyncClient() as client:
        parser = PositiveParserAPI(client=client, max_concurrent=100)
        # await save_products_to_excel(parser, filename="positiv_products.xlsx")
        res = await parser.fetch_product_full_info("01K0731BTZB69PJ0D9J5TRYB23")
        print(res.model_dump(mode="json"))


asyncio.run(main())