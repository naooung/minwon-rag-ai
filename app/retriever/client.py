import logging

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(self, code: str, msg: str):
        super().__init__(f"[{code}] {msg}")
        self.code = code
        self.msg = msg


def normalize_items(body: list | dict) -> list[dict]:
    # 이 API는 flat JSON 배열을 직접 반환하는 경우가 많음
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]

    items = body.get("items")
    if items is None:
        return []

    if isinstance(items, dict):
        item = items.get("item")
        if item is None:
            return []
        if isinstance(item, dict):
            return [item]
        if isinstance(item, list):
            return [x for x in item if isinstance(x, dict)]
        return []

    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]

    return []


async def get(path: str, params: dict) -> list | dict:
    """공통 GET 요청. serviceKey 자동 주입, resultCode 검증."""
    params = {
        "serviceKey": settings.public_api_key,
        "dataType": "json",
        **params,
    }
    url = f"{settings.public_api_base_url}/{path}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    logger.info("API response [%s]: %s", url, data)

    # 이 API는 flat list를 직접 반환함 → 그대로 반환
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        raise APIError("INVALID_FORMAT", f"Unexpected response type: {type(data)}")

    # 일부 공공 API는 "response" 래퍼를 포함
    if "response" in data:
        data = data["response"]

    header = data.get("header", {})
    code = str(header.get("resultCode", "0"))

    if code not in ("0", "00", "200"):
        raise APIError(code, header.get("resultMsg", "Unknown error"))

    return data.get("body", {})
