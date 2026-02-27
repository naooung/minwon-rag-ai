"""
국민권익위원회 민원 빅데이터 Open API 엔드포인트 모음.

사용 API:
  - minSearchDocCnt5    : 키워드 기반 민원 건수 (2022)
  - minTimeSeriseView5  : 키워드 트렌드 시계열 (2022)
  - minWdcloudInfo5     : 연관어 분석 (2022)
  - minPrcsInstInfo     : 기관별 처리 현황 (2025)
  - minActsSubordinateStatutesInfo : 관련 법령 정보 (2025)
"""

from app.retriever.client import get, normalize_items
from app.schemas.models import StatisticItem

_V5 = "minAnalsInfoView5"
_V8 = "minAnalsInfoView8"


async def fetch_doc_count(
    searchword: str,
    date_from: str,
    date_to: str,
    target: str = "pttn",
    search_option: str | None = None,
    omit_duplicate: str | None = None,
) -> list[StatisticItem]:
    """민원 총 건수 조회 (채널별: pttn / dfpt / saeol / prpl).

    Args:
        date_from / date_to: yyyyMMdd 형식
    """
    params: dict = {
        "target": target,
        "dateFrom": date_from,
        "dateTo": date_to,
    }
    if searchword:
        params["searchword"] = searchword
    if search_option:
        params["searchOption"] = search_option
    if omit_duplicate:
        params["omitDuplicate"] = omit_duplicate

    body = await get(f"{_V5}/minSearchDocCnt5", params)
    items = normalize_items(body)

    channels = {"pttn": "청원", "dfpt": "국민신문고", "saeol": "새올행정", "prpl": "공공포털"}
    result: list[StatisticItem] = []
    for item in items:
        for key, label in channels.items():
            if key in item:
                result.append(StatisticItem(label=label, count=int(item[key])))
    return result


async def fetch_time_series(
    searchword: str,
    date_from: str,
    date_to: str,
    period: str = "MONTHLY",
    target: str = "pttn",
    sort_by: str = "NAME",
    sort_order: str = "true",
    main_sub_code: str | None = None,
) -> list[StatisticItem]:
    """키워드 트렌드 시계열 조회.

    Args:
        period: DAILY / MONTHLY / YEARLY
        date_from / date_to: yyyyMMddHHmmss 형식
    """
    params: dict = {
        "period": period,
        "sortBy": sort_by,
        "sortOrder": sort_order,
        "target": target,
        "dateFrom": date_from,
        "dateTo": date_to,
        "searchword": searchword,
    }
    if main_sub_code:
        params["mainSubCode"] = main_sub_code

    body = await get(f"{_V5}/minTimeSeriseView5", params)
    items = normalize_items(body)

    return [
        StatisticItem(
            label=str(item["label"]),
            count=int(item["hits"]),
            extra={"prebRatio": item.get("prebRatio"), "termQuery": item.get("termQuery")},
        )
        for item in items
    ]


async def fetch_word_cloud(
    searchword: str,
    date_from: str,
    date_to: str,
    target: str = "pttn",
    result_count: int = 20,
    omit_duplicate: str | None = None,
) -> list[StatisticItem]:
    """연관어 분석 조회.

    Args:
        date_from / date_to: yyyyMMdd 형식
    """
    params: dict = {
        "searchword": searchword,
        "resultCount": result_count,
        "target": target,
        "dateFrom": date_from,
        "dateTo": date_to,
    }
    if omit_duplicate:
        params["omitDuplicate"] = omit_duplicate

    body = await get(f"{_V5}/minWdcloudInfo5", params)
    items = normalize_items(body)

    return [
        StatisticItem(label=item["label"], count=int(item["value"]))
        for item in items
    ]


async def fetch_institution(
    searchword: str,
    date_from: str,
    date_to: str,
    target: str = "pttn",
    main_sub_code: str = "0",
    search_option: str | None = None,
    omit_duplicate: str | None = None,
) -> list[StatisticItem]:
    """기관별 처리 현황 조회.

    Args:
        date_from / date_to: yyyyMMdd 형식
        main_sub_code: 기관 코드 (0 = 전체)
    """
    params: dict = {
        "target": target,
        "searchword": searchword,
        "dateFrom": date_from,
        "dateTo": date_to,
        "mainSubCode": main_sub_code,
    }
    if search_option:
        params["searchOption"] = search_option
    if omit_duplicate:
        params["omitDuplicate"] = omit_duplicate

    body = await get(f"{_V8}/minPrcsInstInfo", params)
    items = normalize_items(body)

    return [
        StatisticItem(
            label=item["label"],
            count=int(item["hits"]),
            extra={"rank": item.get("rank")},
        )
        for item in items
    ]


async def fetch_statutes(
    searchword: str,
    date_from: str,
    date_to: str,
    target: str = "pttn",
    search_option: str | None = None,
    omit_duplicate: str | None = None,
) -> list[StatisticItem]:
    """관련 법령 정보 조회.

    Args:
        date_from / date_to: yyyyMMdd 형식
    """
    params: dict = {
        "target": target,
        "searchword": searchword,
        "dateFrom": date_from,
        "dateTo": date_to,
    }
    if search_option:
        params["searchOption"] = search_option
    if omit_duplicate:
        params["omitDuplicate"] = omit_duplicate

    body = await get(f"{_V8}/minActsSubordinateStatutesInfo", params)
    items = normalize_items(body)

    return [
        StatisticItem(
            label=item["label"],
            count=int(item["hits"]),
            extra={"rank": item.get("rank"), "ratio": item.get("ratio")},
        )
        for item in items
    ]
