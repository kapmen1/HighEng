from abc import ABC, abstractmethod
from document.schema import PassageResult


class BaseLLM(ABC):
    """LLM 추상 인터페이스. 모든 모델 클라이언트가 이 클래스를 상속."""

    def __init__(self, api_key: str, model_id: str):
        self.api_key = api_key
        self.model_id = model_id
        self.last_usage = {"input_tokens": 0, "output_tokens": 0}

    @abstractmethod
    def analyze_passage(self, english_text: str, passage_no: str) -> PassageResult:
        """영어 지문을 분석하여 PassageResult를 반환"""
        pass

    @abstractmethod
    def validate_key(self) -> bool:
        """API 키 유효성 검증. 유효하면 True."""
        pass
