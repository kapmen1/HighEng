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
    """HWPX XML에서 특정 필드의 텍스트를 교체.

    필드 구조: <hp:fieldBegin name="XXX" ...> ... <hp:t>기존값</hp:t> ... <hp:fieldEnd ...>
    기존 <hp:t> 태그의 내용을 value로 교체한다.
    """
    # fieldBegin ~ fieldEnd 사이의 <hp:t> 텍스트를 교체
    pattern = (
        r'(hp:fieldBegin[^>]*name="' + re.escape(field_name) + r'"[^>]*>.*?<hp:t>)'
        r'(.*?)'
        r'(</hp:t>.*?hp:fieldEnd)'
    )
    replacement = rf'\g<1>{re.escape(value)}\g<3>'

    result = re.sub(pattern, replacement, xml, count=1, flags=re.DOTALL)

    # re.escape로 넣은 이스케이프를 원래대로 복원
    # (re.sub의 replacement에서 \g<1> 등은 처리되지만, value 부분의 이스케이프 필요)
    # 다른 방식으로 처리
    def replacer(match):
        return match.group(1) + value + match.group(3)

    return re.sub(pattern, replacer, xml, count=1, flags=re.DOTALL)


class HwpxBuilder:
    """템플릿 기반 HWPX 문서 생성기."""

    def __init__(self):
        self._passages = []

    def add_passage(self, data: PassageResult):
        """지문 데이터를 추가. build() 시 각각 별도의 HWPX 섹션으로 생성."""
        self._passages.append(data)

    def build(self) -> bytes:
        """HWPX 파일을 바이트로 반환."""
        if not self._passages:
            return b""

        # 첫 번째 지문으로 템플릿 채우기
        return self._build_single(self._passages[0])

    def _build_single(self, data: PassageResult) -> bytes:
        """단일 지문으로 템플릿을 채워 HWPX 바이트 반환."""
        d = data.to_dict()

        # 템플릿 읽기
        with zipfile.ZipFile(TEMPLATE_PATH, 'r') as zin:
            section_xml = zin.read('Contents/section0.xml').decode('utf-8')
            all_files = {name: zin.read(name) for name in zin.namelist()}

        # 필드 채우기
        section_xml = _replace_field_text(section_xml, "No", str(d.get("No", "")))
        section_xml = _replace_field_text(section_xml, "Topic", str(d.get("Topic", "")))
        section_xml = _replace_field_text(section_xml, "TFA", str(d.get("TFA", "")))

        # 줄바꿈 필드 (\n → \r\n)
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

        # 수정된 section0.xml로 HWPX 재조립
        all_files['Contents/section0.xml'] = section_xml.encode('utf-8')

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
            for name, content in all_files.items():
                zout.writestr(name, content)
        buf.seek(0)
        return buf.getvalue()
