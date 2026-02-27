from pydantic import BaseModel, Field


# --- 요청 ---

class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="자연어 분석 질의")


# --- 내부: 쿼리 파싱 결과 (API 파라미터에 직접 매핑) ---

class ParsedQuery(BaseModel):
    searchword: str = Field(..., description="API 검색 키워드")
    date_from: str = Field(..., description="시작일 (yyyyMMdd)")
    date_to: str = Field(..., description="종료일 (yyyyMMdd)")
    target: str = Field("pttn", description="분석 대상 채널 (pttn/dfpt/saeol/prpl)")
    all_channels: bool = Field(False, description="전체 채널 비교 여부")
    use_institution: bool = Field(False, description="기관별 처리 현황 조회 여부")
    use_word_cloud: bool = Field(False, description="연관어 분석 조회 여부")


# --- 내부: 공공 API 통계 항목 ---
# label: API 종류에 따라 기간 / 키워드 / 기관명 / 법령명 등이 올 수 있음

class StatisticItem(BaseModel):
    label: str = Field(..., description="항목 레이블 (기간, 키워드, 기관명 등)")
    count: int = Field(..., description="민원 건수")
    extra: dict | None = Field(None, description="API별 부가 정보 (prevRatio, rank, ratio 등)")


# --- 응답 ---

class AnalyzeResponse(BaseModel):
    summary: str = Field(..., description="3줄 이내 요약")
    statistics: list[StatisticItem] = Field(..., description="근거 통계 목록")
    limitation: str = Field(..., description="한계점 또는 후속 질문")
