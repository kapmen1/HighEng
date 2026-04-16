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
    """
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


class HwpxBuilder:
    """템플릿 기반 HWPX 문서 생성기."""

    def __init__(self):
        self._passages = []

    def add_passage(self, data: PassageResult):
        """지문 데이터를 추가."""
        self._passages.append(data)

    def build(self) -> bytes:
        """모든 지문을 포함한 HWPX 파일을 바이트로 반환."""
        if not self._passages:
            return b""

        # 템플릿 읽기
        with zipfile.ZipFile(TEMPLATE_PATH, 'r') as zin:
            template_section = zin.read('Contents/section0.xml').decode('utf-8')
            content_hpf = zin.read('Contents/content.hpf').decode('utf-8')
            all_files = {name: zin.read(name) for name in zin.namelist()}

        # 각 지문마다 section XML 생성
        for i, passage in enumerate(self._passages):
            filled_xml = _fill_section_xml(template_section, passage)
            section_name = f'Contents/section{i}.xml'
            all_files[section_name] = filled_xml.encode('utf-8')

        # content.hpf 매니페스트에 추가 section 등록
        if len(self._passages) > 1:
            content_hpf = self._update_manifest(content_hpf)

        all_files['Contents/content.hpf'] = content_hpf.encode('utf-8')

        # HWPX 재조립
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zout:
            for name, content in all_files.items():
                zout.writestr(name, content)
        buf.seek(0)
        return buf.getvalue()

    def _update_manifest(self, hpf_xml: str) -> str:
        """content.hpf에 추가 section을 manifest/spine에 등록."""
        # section1, section2, ... 에 대한 manifest item 추가
        manifest_items = ""
        spine_items = ""
        for i in range(1, len(self._passages)):
            manifest_items += (
                f'<opf:item id="section{i}" '
                f'href="Contents/section{i}.xml" '
                f'media-type="application/xml"/>'
            )
            spine_items += f'<opf:itemref idref="section{i}" linear="yes"/>'

        # manifest에 추가 (</opf:manifest> 바로 앞)
        hpf_xml = hpf_xml.replace(
            '</opf:manifest>',
            manifest_items + '</opf:manifest>',
        )

        # spine에 추가 (</opf:spine> 바로 앞)
        hpf_xml = hpf_xml.replace(
            '</opf:spine>',
            spine_items + '</opf:spine>',
        )

        return hpf_xml
