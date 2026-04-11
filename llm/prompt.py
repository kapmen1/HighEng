def build_analysis_prompt(english_text: str, passage_no: str) -> str:
    """영어 지문 분석용 통합 프롬프트 생성.

    1회 API 호출로 번역, 키워드, T/F, 요약을 모두 JSON으로 반환받는다.
    """
    return f"""당신은 한국의 수능 영어 지문 분석 전문가입니다.
아래의 영어 지문을 분석하여 정확히 다음 JSON 형식으로 결과를 출력해주세요.

## 입력 지문
번호: {passage_no}
---
{english_text}
---

## 출력 형식 (JSON)
반드시 아래 형식의 유효한 JSON만 출력하세요. 설명이나 마크다운 없이 순수 JSON만 출력합니다.

{{
  "No": "{passage_no}",
  "Topic": "지문의 핵심 주제를 한국어 명사구로 요약 (15~25자)",
  "Eng": "원문 영어 문장을 | 로 구분하여 나열. 각 문장의 끝에 마침표 포함",
  "Kor": "각 영어 문장에 대응하는 한국어 번역을 | 로 구분. 수능 스타일의 정확한 직역 기반 번역",
  "Flow": "문장 범위: [태그] 요약 형태로 지문 흐름 분석. 줄바꿈(\\n)으로 구분",
  "v1": "영단어 한국어뜻",
  "v2": "영단어 한국어뜻",
  "v3": "...",
  "... (v1~v18까지 총 18개)": "",
  "v18": "영단어 한국어뜻",
  "TF": "1. 영어 T/F 문장 [T / F]\\n2. ...\\n3. ...\\n4. ...\\n5. ... (총 5문제)",
  "TFA": "1.T / 2.F / 3.T / 4.F / 5.T (정답)",
  "TST": "영어 요약문 (2~3문장)\\n한국어 해석"
}}

## 세부 지침

### 번역 (Kor)
- 수능 영어 지문 해석 스타일: 직역을 기본으로 하되 자연스러운 한국어로 작성
- 각 문장은 반드시 대응하는 영어 문장과 1:1 매칭
- 영어 문장과 한국어 문장의 개수가 정확히 동일해야 함

### 흐름 분석 (Flow)
- 3~5개 구간으로 나누어 지문의 논리적 흐름 분석
- 형식: "1-3: [태그] 설명" (줄바꿈 \\n으로 구분)
- 태그 예: [개념정의], [전개], [사례], [대조], [원인분석], [결론] 등

### 핵심 어휘 (v1~v18)
- 지문에서 수능 수준의 핵심 단어 18개 선정
- 형식: "영단어 한국어뜻" (공백으로 구분)
- 동사, 형용사, 명사를 골고루 포함
- 지문에 실제로 등장하는 단어만 선정

### T/F 문제 (TF)
- 5개의 True/False 문제 작성 (영어)
- 지문 내용을 정확히 이해해야 풀 수 있는 수준
- 각 문제 끝에 [T / F] 표기
- 정답 분포: T와 F를 적절히 혼합 (2~3개씩)

### 영어 요약 및 해석 (TST)
- 영어 요약: 2~3문장으로 지문의 핵심 내용 요약
- 한국어 해석: 영어 요약문의 번역
- 줄바꿈(\\n)으로 구분

## 출력 예시
다음은 올바른 출력의 일부입니다:
{{
  "No": "9-1",
  "Topic": "열린 혁신과 개방적 대화가 아이디어 실현에 미치는 영향",
  "Eng": "Imagination gives life to ideas by drawing from the well of received education and on the basis of experience to date. | In the absence of deliberate actions, ideas end up as dead letters and, as Steve Jobs said, result in regrets.",
  "Kor": "상상력은 받은 교육이라는 샘으로부터 이끌어 냄으로써 그리고 지금까지의 경험을 바탕으로 아이디어에 생명을 불어넣는다. | 의도적인 행동이 없으면, 아이디어는 결국 죽은 글자에 불과하게 되고 스티브 잡스가 말했듯이 후회를 초래한다.",
  "v1": "imagination 상상력",
  "v2": "deliberate 의도적인",
  "TF": "1. Ideas can only be brought to life without relying on past experiences or education. [T / F]\\n2. Ideas remaining in the realm of fantasy eventually lead to regrets if not acted upon. [T / F]\\n3. The text argues that the 'one-man show' approach always guarantees superior results. [T / F]\\n4. An open culture allows individuals to communicate on equal terms regardless of their status. [T / F]\\n5. Open innovation is described as an ineffective culture that increases transaction costs. [T / F]",
  "TFA": "1.F / 2.T / 3.F / 4.T / 5.F",
  "TST": "Open innovation and a culture of open conversation transform abstract ideas into reality by fostering equal participation, which ultimately reduces transaction costs and generates surprising outcomes.\\n열린 혁신과 개방적인 대화 문화는 동등한 참여를 촉진하여 추상적인 아이디어를 현실로 바꾸며, 이는 궁극적으로 거래 비용을 줄이고 놀라운 결과를 창출합니다."
}}
"""
