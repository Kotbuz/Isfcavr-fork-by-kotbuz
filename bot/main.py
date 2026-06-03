import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Any

import httpx

from src.core.env import load_env

load_env()

logger = logging.getLogger(__name__)


@dataclass
class ApiError(Exception):
    status_code: int
    detail: str


class ApiClient:
    def __init__(self, base_url: str, transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None
        self._transport = transport
        self._max_retries = 2
        self._backoff_factor = 0.5

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0, read=8.0, write=5.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                http2=False,
                transport=self._transport,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self, method: str, path: str, *, params: dict[str, Any] | None = None, json: Any | None = None
    ) -> Any:
        attempt = 0
        while True:
            try:
                client = await self._get_client()
                url = f"{self.base_url}{path}"
                resp = await client.request(method, url, params=params, json=json)

                if 200 <= resp.status_code < 300:
                    return resp.json() if resp.content else None

                if resp.status_code in {503, 504} and attempt < self._max_retries:
                    delay = self._backoff_factor * (2**attempt) + random.uniform(0, 0.1)
                    logger.warning(
                        "Temporary API error %s for %s %s, retrying after %.2fs",
                        resp.status_code,
                        method,
                        path,
                        delay,
                    )
                    attempt += 1
                    await asyncio.sleep(delay)
                    continue

                detail = None
                try:
                    payload = resp.json()
                    if isinstance(payload, dict):
                        detail = payload.get("detail")
                except Exception:
                    detail = None

                raise ApiError(status_code=resp.status_code, detail=detail or resp.text or "API error")
            except httpx.TimeoutException as exc:
                if attempt < self._max_retries:
                    delay = self._backoff_factor * (2**attempt) + random.uniform(0, 0.1)
                    logger.warning("Timeout on API request %s %s, retrying after %.2fs", method, path, delay)
                    attempt += 1
                    await asyncio.sleep(delay)
                    continue
                logger.error("API request timeout: %s", exc)
                raise ApiError(status_code=504, detail="API request timeout") from exc
            except httpx.RequestError as exc:
                if attempt < self._max_retries:
                    delay = self._backoff_factor * (2**attempt) + random.uniform(0, 0.1)
                    logger.warning(
                        "Network error on API request %s %s, retrying after %.2fs: %s", method, path, delay, exc
                    )
                    attempt += 1
                    await asyncio.sleep(delay)
                    continue
                logger.error("API connection error: %s", exc)
                raise ApiError(status_code=503, detail="API service unavailable") from exc
            except ApiError:
                raise
            except Exception as exc:
                logger.error("Unexpected API error: %s", exc)
                raise ApiError(status_code=500, detail="Unexpected error") from exc

    async def create_box(self) -> dict[str, Any]:
        return await self._request("POST", "/box")

    async def send_feedback(self, box_uuid: str, text: str) -> dict[str, Any]:
        return await self._request("POST", f"/box/{box_uuid}/feedback", json={"text": text})

    async def get_box_feedbacks(self, box_uuid: str, token: str) -> dict[str, Any]:
        return await self._request("GET", f"/box/{box_uuid}", params={"token": token})

    async def send_reply(self, feedback_id: int, token: str, text: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/feedback/{feedback_id}/reply",
            params={"token": token},
            json={"text": text},
        )
