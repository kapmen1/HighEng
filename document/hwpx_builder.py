"""템플릿 HWPX 파일의 필드를 채워 넣는 방식으로 HWPX 문서를 생성.

template.py와 동일한 필드 구조 사용:
- No, Topic, Flow, TF, TFA, TST
- n1~n11, e1~e11, k1~k11
- v1~v18
"""
import io
import os
import re
import zipfile

from document.schema import PassageResult
from utils.text_processing import split_sentences

# 템플릿 파일 경로
TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates", "템플릿.hwpx",
)


def _replace_field_text(xml: str, field_name: str, value: str) -> str:
    """HWPX XML에서 특정 필드의 텍스트를 교체."""
    pattern = (
        r'(hp:fieldBegin[^>]*name="' + re.escape(field_name) + r'"[^>]*>.*?<hp:t>)'
        r'(.*?)'
        r'(</hp:t>.*?hp:fieldEnd)'
    )

    def replacer(match):
        return match.group(1) + value + match.group(3)

    return re.sub(pattern, replacer, xml, count=1, flags=re.DOTALL)


def _fill_section_xml(section_xml: str, data: PassageResult) -> str:
    """템플릿 section XML에 지문 데이터를 채워넣기."""
    d = data.to_dict()

    # 기본 필드
    section_xml = _replace_field_text(section_xml, "No", str(d.get("No", "")))
    section_xml = _replace_field_text(section_xml, "Topic", str(d.get("Topic", "")))
    section_xml = _replace_field_text(section_xml, "TFA", str(d.get("TFA", "")))

    # 줄바꿈 필드
    for field in ["Flow", "TF", "TST"]:
        value = str(d.get(field, ""))
        section_xml = _replace_field_text(section_xml, field, value)

    # 본문 문장
    eng_list = split_sentences(d.get("Eng", ""))
    kor_list = split_sentences(d.get("Kor", ""))
    max_idx = max(len(eng_list), len(kor_list))

    for j in range(1, 12):
        idx = j - 1
        if idx < max_idx:
            section_xml = _replace_field_text(section_xml, f"n{j}", str(j))
            section_xml = _replace_field_text(
                section_xml, f"e{j}",
                eng_list[idx] if idx < len(eng_list) else " "
            )
            section_xml = _replace_field_text(
                section_xml, f"k{j}",
                kor_list[idx] if idx < len(kor_list) else " "
            )
        else:
            section_xml = _replace_field_text(section_xml, f"n{j}", " ")
            section_xml = _replace_field_text(section_xml, f"e{j}", " ")
            section_xml = _replace_field_text(section_xml, f"k{j}", " ")

    # VOCA 정리 (template.py와 동일)
    voca_items = []
    for v in range(1, 19):
        val = d.get(f"v{v}", "")
        if isinstance(val, str):
            val = val.strip()
        if val:
            voca_items.append(val)

    for i in range(1, 19):
        if i <= len(voca_items):
            section_xml = _replace_field_text(section_xml, f"v{i}", voca_items[i - 1])
        else:
            section_xml = _replace_field_text(section_xml, f"v{i}", " ")

    # 레이아웃 캐시 제거 (한글이 열 때 자동 재계산)
    section_xml = re.sub(
        r'<hp:linesegarray>.*?</hp:linesegarray>',
        '',
        section_xml,
        flags=re.DOTALL,
    )

    return section_xml


def _extract_section_body(section_xml: str) -> str:
    """section XML에서 <hs:sec ...> 루트 태그 내부의 본문만 추출."""
    # 여는 태그 제거
    body = re.sub(r'^<\?xml[^>]*\?>\s*<hs:sec[^>]*>', '', section_xml, count=1)
    # 닫는 태그 제거
    body = re.sub(r'</hs:sec>\s*$', '', body)
    return body


class HwpxBuilder:
    """템플릿 기반 HWPX 문서 생성기."""

    def __init__(self):
        self._passages = []

    def add_passage(self, data: PassageResult):
        """지문 데이터를 추가."""
        self._passages.append(data)

    def build(self) -> bytes:
        """모든 지문을 하나의 section0.xml에 합쳐서 HWPX 바이트 반환."""
        if not self._passages:
            return b""

        # 템플릿 읽기
        with zipfile.ZipFile(TEMPLATE_PATH, 'r') as zin:
            template_section = zin.read('Contents/section0.xml').decode('utf-8')
            all_files = {name: zin.read(name) for name in zin.namelist()}

        if len(self._passages) == 1:
            # 단일 지문: 그대로 채우기
            filled = _fill_section_xml(template_section, self._passages[0])
            all_files['Contents/section0.xml'] = filled.encode('utf-8')
        else:
            # 다중 지문: 각 지문을 채운 후 본문을 하나의 section에 연결
            # 첫 번째 지문을 기본 section으로 사용
            first_filled = _fill_section_xml(template_section, self._passages[0])

            # 닫는 태그 앞에 나머지 지문의 본문을 삽입
            additional_bodies = ""
            for passage in self._passages[1:]:
                filled = _fill_section_xml(template_section, passage)
                body = _extract_section_body(filled)
                additional_bodies += body

            # </hs:sec> 바로 앞에 삽입
            first_filled = first_filled.replace(
                '</hs:sec>',
                additional_bodies + '</hs:sec>',
            )
            all_files['Contents/section0.xml'] = first_filled.encode('utf-8')

        # HWPX 재조립
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
            for name, content in all_files.items():
                zout.writestr(name, content)
        buf.seek(0)
        return buf.getvalue()
