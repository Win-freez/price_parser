import logging
import functools
import asyncio
from typing import Any, Callable, TypeVar, Optional
from httpx import RequestError, HTTPStatusError, TimeoutException

logger = logging.getLogger(__name__)
T = TypeVar('T')


class ErrorHandler:
    """Класс для централизованной обработки ошибок"""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @staticmethod
    def async_error_handler(func: Callable[..., Any]) -> Callable[..., Any]:
        """Декоратор для обработки ошибок в асинхронных методах"""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Optional[Any]:
            try:
                return await func(*args, **kwargs)
            except TimeoutException:
                logger.error(f"Timeout в {func.__name__}")
            except RequestError as e:
                logger.error(f"Ошибка сети в {func.__name__}: {e}")
            except HTTPStatusError as e:
                logger.error(f"HTTP ошибка в {func.__name__}: {e.response.status_code}")
            except Exception as e:
                logger.exception(f"Неожиданная ошибка в {func.__name__}: {e}")
            return None

        return wrapper

    def async_error_handler_with_retry(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Декоратор с повторными попытками для асинхронных методов"""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Optional[Any]:
            for attempt in range(self.max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        logger.error(f"Ошибка после {self.max_retries} попыток в {func.__name__}: {e}")
                        return None
                    logger.warning(f"Попытка {attempt + 1}/{self.max_retries} в {func.__name__}: {e}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
            return None

        return wrapper


    @staticmethod
    def sync_error_handler(func: Callable[..., Any]) -> Callable[..., Any]:
        """Декоратор для обработки ошибок в синхронных методах"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Ошибка в {func.__name__}: {e}")
                return None

        return wrapper