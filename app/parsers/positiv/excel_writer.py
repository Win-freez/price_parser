import asyncio

from app.parsers.positiv.positiv import PositiveParserAPI


async def save_products_to_excel(parser: PositiveParserAPI, filename: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"

    headers = [
        "Категория", "public_id", "name", "slug", "imageUrl", "vendorCode", "code",
        "description", "snippet", "monthWarranty", "count", "unitOfMeasurement",
        "isAvailable", "stockStatus", "price", "currency", "isNew",
        "isPopular", "isSeasonal", "isGift", "links1c", "isPublished",
        "publishedDate", "unpublishedDate", "createdAt"
    ]
    ws.append(headers)

    async for category_name, products in parser.get_all_products_short_info():
        ws.append([f"{category_name}"] + [""] * (len(headers) - 1))
        for product in products:
            row = [
                category_name,
                product.public_id,
                product.name,
                product.slug,
                str(product.imageUrl) if product.imageUrl else "",
                product.vendorCode,
                product.code,
                product.description,
                product.snippet,
                product.monthWarranty or "",
                product.count,
                product.unitOfMeasurement,
                product.isAvailable,
                product.stockStatus,
                product.price,
                product.currency,
                product.isNew,
                product.isPopular,
                product.isSeasonal,
                product.isGift,
                product.links1c,
                product.isPublished,
                product.publishedDate.isoformat() if product.publishedDate else "",
                product.unpublishedDate.isoformat() if product.unpublishedDate else "",
                product.createdAt.isoformat() if product.createdAt else "",
            ]
            ws.append(row)

        print(f"Записаны {len(products)} товаров категории {category_name}")

    wb.save(filename)
    wb.close()
    print(f"Excel сохранён в {filename}")


async def main():
    import httpx
    async with httpx.AsyncClient() as client:
        parser = PositiveParserAPI(client=client, max_concurrent=10)
        await save_products_to_excel(parser, "Товары.xlsx")


asyncio.run(main())