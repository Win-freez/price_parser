import asyncio


async def run_parser(parser, attempts=3, timeout=5):
    """Запускает один парсер с retries по таймауту или исключениям"""
    for attempt in range(1, attempts + 1):
        try:
            return await asyncio.wait_for(parser.search_products(), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"[{parser.__class__.__name__}] Таймаут на попытке {attempt}/{attempts}")
        except Exception as e:
            print(f"[{parser.__class__.__name__}] Ошибка на попытке {attempt}/{attempts}: {e}")
    return None