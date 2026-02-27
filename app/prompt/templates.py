"""프롬프트 템플릿 및 LLM 출력 파서."""

import json
import re

from app.schemas.models import StatisticItem

SYSTEM_PROMPT = """당신은 민원 빅데이터 분석 전문가입니다.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

{
  "summary": "핵심 트렌드 요약 (최대 3줄, 줄바꿈은 \\n으로 구분)",
  "limitation": "데이터 한계점 또는 후속 질문 (1~2문장)"
}

규칙:
- 제공된 통계 수치 외의 수치를 절대 만들지 마세요.
- 제공된 데이터가 없으면 summary에 "조회된 데이터가 부족하여 분석이 어렵습니다."라고 작성하세요.
- summary는 반드시 아래 순서로 작성하세요:
  1줄: 전체 기간의 민원 건수와 대표 추세 (증가/감소/변동)
  2줄: 가장 많은 건수를 기록한 시점과 수치, 전월 대비 증감률(prebRatio)이 가장 큰 시점
  3줄: 주목할 만한 패턴 또는 이상치 (급등·급락 구간)
- limitation은 실제 데이터를 기반으로 작성하세요. 데이터가 충분하면 "데이터 부족"이라고 쓰지 마세요.
  대신 분석에서 알 수 없는 것(원인, 지역별 분포, 채널 비교 등)을 후속 질문으로 제시하세요.
- 항상 한국어로만 답해주세요.
"""


def _format_label(label: str) -> str:
    """yyyyMMdd 형태의 레이블을 사람이 읽기 쉬운 형태로 변환."""
    if re.fullmatch(r"\d{8}", label):
        return f"{label[:4]}년 {label[4:6]}월"
    return label


def format_statistics(statistics: list[StatisticItem]) -> str:
    if not statistics:
        return "조회된 데이터 없음"
    lines = []
    for item in statistics:
        label = _format_label(item.label)
        line = f"- {label}: {item.count:,}건"
        if item.extra:
            ratio = item.extra.get("prebRatio")
            if ratio is not None:
                sign = "+" if float(ratio) > 0 else ""
                line += f" (전월 대비 {sign}{ratio}%)"
        lines.append(line)
    return "\n".join(lines)


def build_messages(query: str, statistics: list[StatisticItem]) -> list[dict]:
    stats_text = format_statistics(statistics)
    user_content = (
        f"분석 질의: {query}\n\n"
        f"[조회된 통계 데이터]\n{stats_text}\n\n"
        "위 데이터를 기반으로 분석 결과를 JSON으로 반환하세요."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def parse_llm_output(raw: str) -> tuple[str, str]:
    """LLM 출력 텍스트에서 summary, limitation 추출."""
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return data.get("summary", ""), data.get("limitation", "")
        except json.JSONDecodeError:
            pass
    # fallback: 전체 텍스트를 summary로
    return raw.strip(), ""
