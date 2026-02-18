import asyncio
import time
from typing import Optional

import httpx
from httpx import Response

from app.core.config import settings
from app.core.logger import logger


class HttpClient:
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            # 配置代理
            proxies = settings.HTTP_PROXY if settings.HTTP_PROXY else None
            cls._client = httpx.AsyncClient(
                proxy=proxies,
                timeout=30.0,
                headers={
                    "User-Agent": f"{settings.PROJECT_NAME}/1.0",
                    "Accept": "application/json"
                }
            )
            logger.info(f"Initialized HTTP Client with proxies: {proxies if proxies else 'None'}")
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.aclose()
            cls._client = None
            logger.info("HTTP Client closed.")

    @classmethod
    async def request(
            cls,
            method: str,
            url: str,
            retries: int = 3,
            retry_delay: int = 1,
            **kwargs
    ) -> Response | None:
        """
        封装的请求方法
        :param method: GET, POST, etc.
        :param url: 请求地址
        :param retries: 重试次数 (默认3次)
        :param retry_delay: 重试间隔 (秒)
        :param kwargs: 传递给 httpx 的其他参数
        :return: httpx.Response
        """
        client = cls.get_client()
        current_retry = 0

        log_prefix = f"[{method.upper()}] {url}"

        while current_retry <= retries:
            start_time = time.time()
            try:
                logger.debug(f"Requesting: {log_prefix} | Try: {current_retry + 1}/{retries + 1}")

                response = await client.request(method, url, **kwargs)
                process_time = (time.time() - start_time) * 1000
                status_code = response.status_code
                log_msg = f"Finished: {log_prefix} | Status: {status_code} | Time: {process_time:.2f}ms"

                if 200 <= status_code < 300:
                    logger.info(log_msg)
                elif 300 <= status_code < 400:
                    logger.warning(log_msg)
                else:
                    logger.error(log_msg)

                return response

            except httpx.RequestError as exc:
                logger.warning(f"Request Error: {log_prefix} | Error: {exc} | Retrying in {retry_delay}s...")
                current_retry += 1
                if current_retry > retries:
                    logger.critical(f"Max retries reached for {log_prefix}")
                    raise exc

                await asyncio.sleep(retry_delay)

            except Exception as e:
                logger.error(f"Unexpected Error: {log_prefix} | {e}")
                raise e
        return None

    @classmethod
    async def get(cls, url: str, **kwargs):
        return await cls.request("GET", url, **kwargs)

    @classmethod
    async def post(cls, url: str, **kwargs):
        return await cls.request("POST", url, **kwargs)
