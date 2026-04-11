import anthropic

from document.schema import PassageResult, parse_llm_response
from .base import BaseLLM
from .prompt import build_analysis_prompt


class ClaudeLLM(BaseLLM):
    """Anthropic Claude API 클라이언트"""

    def __init__(self, api_key: str, model_id: str):
        super().__init__(api_key, model_id)
        self.client = anthropic.Anthropic(api_key=api_key)

    def analyze_passage(self, english_text: str, passage_no: str) -> PassageResult:
        """영어 지문을 Claude로 분석"""
        prompt = build_analysis_prompt(english_text, passage_no)
        message = self.client.messages.create(
            model=self.model_id,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        self.last_usage = {
            "input_tokens": getattr(message.usage, 'input_tokens', 0) or 0,
            "output_tokens": getattr(message.usage, 'output_tokens', 0) or 0,
        }
        return parse_llm_response(message.content[0].text)

    def validate_key(self) -> bool:
        """Claude API 키 유효성 검증"""
        try:
            self.client.messages.create(
                model=self.model_id,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}],
            )
            return True
        except Exception:
            return False
