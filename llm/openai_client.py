from openai import OpenAI

from document.schema import PassageResult, parse_llm_response
from .base import BaseLLM
from .prompt import build_analysis_prompt


class OpenAILLM(BaseLLM):
    """OpenAI ChatGPT API 클라이언트"""

    def __init__(self, api_key: str, model_id: str):
        super().__init__(api_key, model_id)
        self.client = OpenAI(api_key=api_key)

    def analyze_passage(self, english_text: str, passage_no: str) -> PassageResult:
        """영어 지문을 ChatGPT로 분석"""
        prompt = build_analysis_prompt(english_text, passage_no)
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
        )
        if response.usage:
            self.last_usage = {
                "input_tokens": response.usage.prompt_tokens or 0,
                "output_tokens": response.usage.completion_tokens or 0,
            }
        return parse_llm_response(response.choices[0].message.content)

    def validate_key(self) -> bool:
        """OpenAI API 키 유효성 검증"""
        try:
            self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )
            return True
        except Exception:
            return False
