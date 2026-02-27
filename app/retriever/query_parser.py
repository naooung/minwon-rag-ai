"""자연어 질의 → API 파라미터 변환 (규칙 기반)."""

import calendar
import re
from datetime import date

from app.schemas.models import ParsedQuery

_STOPWORDS = {
    "분석", "분석해줘", "알려줘", "보여줘", "해줘", "줘",
    "어때", "어떻게", "됐어", "추이", "트렌드", "현황", "통계",
    "데이터", "관련", "대한", "최근", "올해", "작년",
}

_INTENT_CHANNELS = {"채널", "채널별", "비교", "국민신문고", "새올", "공공포털", "채널비교"}
_INTENT_INSTITUTION = {"기관", "기관별", "처리기관", "지역", "지역별", "지자체", "시군구"}
_INTENT_WORD_CLOUD = {"연관어", "연관", "키워드", "관련어", "연관키워드"}


def _extract_dates(query: str) -> tuple[str, str]:
    """연도/월 패턴으로 date_from, date_to(yyyyMMdd) 추출."""
    year_m = re.search(r"(20\d{2})", query)
    month_m = re.search(r"(\d{1,2})월", query)

    if year_m:
        year = int(year_m.group(1))
        if month_m:
            month = int(month_m.group(1))
            last_day = calendar.monthrange(year, month)[1]
            return f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
        return f"{year}0101", f"{year}1231"

    # 기본: 직전 연도
    today = date.today()
    prev = today.year - 1
    return f"{prev}0101", f"{prev}1231"


def _extract_searchword(query: str) -> str:
    """날짜/불용어 제거 후 핵심 키워드 추출."""
    text = re.sub(r"20\d{2}년?", "", query)
    text = re.sub(r"\d{1,2}월", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    tokens = [t for t in text.split() if t not in _STOPWORDS]
    return " ".join(tokens).strip() or query.strip()


def _detect_intent(query: str) -> tuple[bool, bool, bool]:
    """질의 토큰에서 의도 플래그 반환: (all_channels, use_institution, use_word_cloud)."""
    tokens = set(query.split())
    all_channels = bool(tokens & _INTENT_CHANNELS)
    use_institution = bool(tokens & _INTENT_INSTITUTION)
    use_word_cloud = bool(tokens & _INTENT_WORD_CLOUD)
    return all_channels, use_institution, use_word_cloud


def parse_query(query: str) -> ParsedQuery:
    date_from, date_to = _extract_dates(query)
    searchword = _extract_searchword(query)
    all_channels, use_institution, use_word_cloud = _detect_intent(query)
    return ParsedQuery(
        searchword=searchword,
        date_from=date_from,
        date_to=date_to,
        all_channels=all_channels,
        use_institution=use_institution,
        use_word_cloud=use_word_cloud,
    )
