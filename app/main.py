import asyncio
from asyncio import create_task
from pprint import pprint

from app.parsers.etm import EtmParser
from app.parsers.ozon import OzonParser
from app.parsers.parser import Parser
from app.parsers.vseinstrumenti import VseinstrumentiParser


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



async def main(word: str, attempts=3, timeout=20):
    async with Parser.get_browser() as browser:
        parsers = [
            OzonParser(browser=browser, word=word),
            VseinstrumentiParser(browser=browser, word=word),
            EtmParser(browser=browser, word=word)
        ]
        tasks = [create_task(run_parser(p, attempts=attempts, timeout=timeout)) for p in parsers]
        results = await asyncio.gather(*tasks)
        return results




if __name__ == "__main__":
    pprint(asyncio.run(main("C9F34116")))
