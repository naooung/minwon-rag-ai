import asyncio

from fastapi import APIRouter, HTTPException

from app.llm.qwen import qwen_model
from app.prompt.templates import build_messages, parse_llm_output
from app.retriever.public_api import (
    fetch_doc_count,
    fetch_institution,
    fetch_time_series,
    fetch_word_cloud,
)
from app.retriever.query_parser import parse_query
from app.schemas.models import AnalyzeRequest, AnalyzeResponse, StatisticItem

router = APIRouter()


def _to_datetime(date_str: str) -> str:
    """yyyyMMdd → yyyyMMddHHmmss (시계열 API 형식)."""
    return date_str + "000000"


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    # 1. 쿼리 파싱
    parsed = parse_query(request.query)

    # 2. 의도에 따라 조회할 API 목록 구성 (병렬 실행)
    _channels = ["pttn", "dfpt", "saeol", "prpl"] if parsed.all_channels else [parsed.target]

    tasks = []

    # 채널별 총 건수: all_channels면 각 채널을 개별 호출
    for ch in _channels:
        tasks.append(fetch_doc_count(
            searchword=parsed.searchword,
            date_from=parsed.date_from,
            date_to=parsed.date_to,
            target=ch,
        ))

    # 시계열 (기본 포함)
    tasks.append(fetch_time_series(
        searchword=parsed.searchword,
        date_from=_to_datetime(parsed.date_from),
        date_to=_to_datetime(parsed.date_to),
        target=parsed.target,
    ))

    # 기관별
    if parsed.use_institution:
        tasks.append(fetch_institution(
            searchword=parsed.searchword,
            date_from=parsed.date_from,
            date_to=parsed.date_to,
            target=parsed.target,
        ))

    # 연관어
    if parsed.use_word_cloud:
        tasks.append(fetch_word_cloud(
            searchword=parsed.searchword,
            date_from=parsed.date_from,
            date_to=parsed.date_to,
            target=parsed.target,
        ))

    try:
        results = await asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"공공 API 오류: {e}")

    statistics: list[StatisticItem] = [item for batch in results for item in batch]

    # 3. 프롬프트 구성 및 LLM 추론
    # generate()는 CPU/GPU 블로킹 연산이므로 thread executor에서 실행해 event loop를 보호
    messages = build_messages(request.query, statistics)
    loop = asyncio.get_event_loop()
    try:
        raw_output = await loop.run_in_executor(None, qwen_model.generate, messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 추론 오류: {e}")

    # 4. 응답 파싱
    summary, limitation = parse_llm_output(raw_output)

    return AnalyzeResponse(
        summary=summary or "분석 결과를 생성하지 못했습니다.",
        statistics=statistics,
        limitation=limitation or "추가 데이터가 필요합니다.",
    )
