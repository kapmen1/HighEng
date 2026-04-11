from google import genai

from document.schema import PassageResult, parse_llm_response
from .base import BaseLLM
from .prompt import build_analysis_prompt


class GeminiLLM(BaseLLM):
    """Google Gemini API 클라이언트 (google-genai 패키지 사용)"""

    def __init__(self, api_key: str, model_id: str):
        super().__init__(api_key, model_id)
        self.client = genai.Client(api_key=api_key)

    def analyze_passage(self, english_text: str, passage_no: str) -> PassageResult:
        """영어 지문을 Gemini로 분석"""
        prompt = build_analysis_prompt(english_text, passage_no)
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
        )
        usage = response.usage_metadata
        self.last_usage = {
            "input_tokens": getattr(usage, 'prompt_token_count', 0) or 0,
            "output_tokens": (getattr(usage, 'candidates_token_count', 0) or 0)
                           + (getattr(usage, 'thoughts_token_count', 0) or 0),
        }
        return parse_llm_response(response.text)

    def validate_key(self) -> bool:
        """Gemini API 키 유효성 검증"""
        try:
            self.client.models.generate_content(
                model=self.model_id,
                contents="Hello",
            )
            return True
        except Exception:
            return False
