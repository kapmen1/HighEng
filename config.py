# HighEng 전역 설정

# 세부 모델 카탈로그: 모델군 → 세부 모델 리스트
MODEL_CATALOG = {
    "Gemini": [
        {"label": "Gemini 2.5 Flash-Lite", "model_id": "gemini-2.5-flash-lite", "input_price": 0.10,  "output_price": 0.40,  "tier": "하", "note": "최저가, 간단한 지문에 적합"},
        {"label": "Gemini 2.5 Flash",      "model_id": "gemini-2.5-flash",      "input_price": 0.15,  "output_price": 3.50,  "tier": "중", "note": "가성비 추천"},
        {"label": "Gemini 3 Flash",         "model_id": "gemini-3-flash",        "input_price": 0.50,  "output_price": 3.00,  "tier": "중", "note": "최신 Flash"},
        {"label": "Gemini 3 Pro",           "model_id": "gemini-3-pro",          "input_price": 2.00,  "output_price": 12.00, "tier": "상", "note": "고품질"},
    ],
    "Claude": [
        {"label": "Claude Haiku 4.5",  "model_id": "claude-haiku-4-5-20251001",  "input_price": 1.00,  "output_price": 5.00,  "tier": "하", "note": "빠르고 저렴"},
        {"label": "Claude Sonnet 4.6", "model_id": "claude-sonnet-4-6-20250514", "input_price": 3.00,  "output_price": 15.00, "tier": "중", "note": "균형잡힌 품질"},
        {"label": "Claude Opus 4.6",   "model_id": "claude-opus-4-6-20250414",   "input_price": 15.00, "output_price": 75.00, "tier": "상", "note": "최고 품질"},
    ],
    "ChatGPT": [
        {"label": "GPT-4o mini", "model_id": "gpt-4o-mini", "input_price": 0.15,  "output_price": 0.60,  "tier": "하", "note": "최저가 수준"},
        {"label": "GPT-4o",      "model_id": "gpt-4o",      "input_price": 2.50,  "output_price": 10.00, "tier": "상", "note": "고품질"},
    ],
}

# 지문 처리 상수
MAX_SENTENCES = 11  # 본문 최대 문장 수
VOCA_COUNT = 18     # 핵심 어휘 개수
TF_COUNT = 5        # T/F 문제 수


def get_model_labels(provider: str) -> list[str]:
    """해당 모델군의 세부 모델 레이블 리스트 반환"""
    return [entry["label"] for entry in MODEL_CATALOG[provider]]


def get_model_info(provider: str, label: str) -> dict:
    """해당 모델군 + 레이블에 해당하는 모델 정보(model_id, cost, note) 반환"""
    for entry in MODEL_CATALOG[provider]:
        if entry["label"] == label:
            return entry
    raise ValueError(f"모델을 찾을 수 없습니다: {provider} / {label}")
