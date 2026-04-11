import json
import re
from dataclasses import dataclass, fields
from typing import Optional


@dataclass
class PassageResult:
    """LLM이 생성한 영어 지문 분석 결과 스키마.

    기존 자동화 패키지/JSON.txt 구조와 호환.
    """
    No: str = ""
    Topic: str = ""
    Eng: str = ""
    Kor: str = ""
    Flow: str = ""
    TF: str = ""
    TFA: str = ""
    TST: str = ""
    # VOCA v1~v18
    v1: str = ""
    v2: str = ""
    v3: str = ""
    v4: str = ""
    v5: str = ""
    v6: str = ""
    v7: str = ""
    v8: str = ""
    v9: str = ""
    v10: str = ""
    v11: str = ""
    v12: str = ""
    v13: str = ""
    v14: str = ""
    v15: str = ""
    v16: str = ""
    v17: str = ""
    v18: str = ""

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (빈 문자열 필드 제외)"""
        return {f.name: getattr(self, f.name)
                for f in fields(self) if getattr(self, f.name)}

    def get_voca_list(self) -> list:
        """v1~v18 중 값이 있는 어휘만 리스트로 반환"""
        result = []
        for i in range(1, 19):
            val = getattr(self, f"v{i}", "").strip()
            if val:
                result.append(val)
        return result

    @classmethod
    def from_json_str(cls, json_str: str) -> 'PassageResult':
        """LLM 응답 JSON 문자열을 파싱하여 PassageResult 생성.

        마크다운 코드블록(```json ... ```)도 처리.
        """
        cleaned = json_str.strip()

        # 마크다운 코드블록 제거
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        data = json.loads(cleaned)

        # dataclass 필드명과 매칭되는 값만 추출
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


def parse_llm_response(response_text: str) -> PassageResult:
    """LLM 응답에서 JSON을 추출하고 PassageResult로 변환.

    3단계 폴백:
    1. 직접 파싱
    2. ```json ... ``` 블록 추출
    3. 첫 번째 { ... } 블록 추출
    """
    # 1차: 직접 파싱
    try:
        return PassageResult.from_json_str(response_text)
    except (json.JSONDecodeError, ValueError):
        pass

    # 2차: 코드블록 추출
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if match:
        try:
            return PassageResult.from_json_str(match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    # 3차: 첫 번째 { ... } 블록
    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if match:
        return PassageResult.from_json_str(match.group(0))

    raise ValueError("LLM 응답에서 유효한 JSON을 찾을 수 없습니다.")
