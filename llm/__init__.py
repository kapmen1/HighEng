from .base import BaseLLM
from .gemini_client import GeminiLLM


def create_llm(provider: str, api_key: str, model_id: str) -> BaseLLM:
    """선택한 모델에 맞는 LLM 객체를 생성하여 반환"""
    if provider == "Gemini":
        return GeminiLLM(api_key, model_id)
    elif provider == "Claude":
        from .claude_client import ClaudeLLM
        return ClaudeLLM(api_key, model_id)
    elif provider == "ChatGPT":
        from .openai_client import OpenAILLM
        return OpenAILLM(api_key, model_id)
    raise ValueError(f"지원하지 않는 모델: {provider}")
