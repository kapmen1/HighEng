import re


def split_passages(text: str) -> list[str]:
    """여러 지문이 포함된 텍스트를 개별 지문으로 분리.

    분리 전략 (우선순위):
    1. 번호 기반: 줄 시작이 '1.', '2.', '1)', '(1)' 등의 패턴
    2. 빈 줄 기반: 2줄 이상 연속 빈 줄
    3. 분리 불가 시 전체를 단일 지문으로 반환
    """
    text = text.strip()
    if not text:
        return []

    # 전략 1: 번호 패턴 (줄 시작 위치에서만 매칭)
    markers = list(re.finditer(r'(?:^|\n)[ \t]*\(?(\d+)[.\)]\)?[ \t]+', text))
    if len(markers) >= 2 and markers[0].group(1) == '1':
        positions = [m.start() for m in markers]
        positions.append(len(text))
        parts = []
        for i in range(len(positions) - 1):
            chunk = text[positions[i]:positions[i + 1]].strip()
            # 번호 접두사 제거
            chunk = re.sub(r'^[ \t]*\(?\d+[.\)]\)?[ \t]+', '', chunk)
            if chunk:
                parts.append(chunk)
        if len(parts) >= 2:
            return parts

    # 전략 2: 2줄 이상 연속 빈 줄
    parts = re.split(r'\n[ \t]*\n[ \t]*\n', text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) >= 2:
        return parts

    # 단일 지문
    return [text]


def split_sentences(text: str) -> list:
    """영어/한국어 텍스트를 문장 단위로 분할.

    기존 자동화 패키지/template.py의 로직을 이식.
    1순위: '|' 구분자로 분할
    2순위: 마침표/물음표/느낌표 뒤 공백 기준 자동 분할
    """
    if not text:
        return []
    text = re.sub(r'\[해석\]', '', text)
    text = ' '.join(text.split())

    # 1. 강제 분할 기호('|') 우선 처리
    if '|' in text:
        return [s.strip() for s in text.split('|') if s.strip()]

    # 2. 문장 끝 기준 자동 분할
    marked_text = re.sub(r'([.?!][\"\'\)\]]*)\s+', r'\1\x00', text)
    sentences = marked_text.split('\x00')
    return [s.strip() for s in sentences if s.strip()]
