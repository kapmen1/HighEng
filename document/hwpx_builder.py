from hwpx import HwpxDocument

from document.schema import PassageResult
from utils.text_processing import split_sentences


class HwpxBuilder:
    """HWPX 문서 생성기. DocxBuilder와 동일한 레이아웃을 HWPX로 재현."""

    def __init__(self):
        self.doc = HwpxDocument.new()
        self._first_passage = True

    def add_passage(self, data: PassageResult):
        """지문 1개의 전체 레이아웃 추가"""
        d = data.to_dict()

        # 두 번째 지문부터 새 섹션(페이지) 추가
        if not self._first_passage:
            self.doc.add_section()
        self._first_passage = False

        # 1. 헤더: 지문 번호 + 주제
        self.doc.add_paragraph(f"[{d.get('No', '')}] {d.get('Topic', '')}")

        # 2. 본문 테이블 (번호 / 영어 / 한국어)
        self._add_eng_kor_table(d.get('Eng', ''), d.get('Kor', ''))

        # 3. FLOW 섹션
        self._add_flow_section(d.get('Flow', ''))

        # 4. VOCA 섹션
        self._add_voca_section(data)

        # 5. T/F 섹션
        self._add_tf_section(d.get('TF', ''), d.get('TFA', ''))

        # 6. SUMMARY 섹션
        self._add_summary_section(d.get('TST', ''))

    def _add_eng_kor_table(self, eng_text: str, kor_text: str):
        """영어-한국어 대조 테이블"""
        self.doc.add_paragraph("■ 본문 (TEXT)")

        eng_sentences = split_sentences(eng_text)
        kor_sentences = split_sentences(kor_text)
        row_count = max(len(eng_sentences), len(kor_sentences))

        if row_count == 0:
            return

        table = self.doc.add_table(rows=row_count, cols=3)

        for i in range(row_count):
            table.set_cell_text(i, 0, str(i + 1))
            eng = eng_sentences[i] if i < len(eng_sentences) else ""
            table.set_cell_text(i, 1, eng)
            kor = kor_sentences[i] if i < len(kor_sentences) else ""
            table.set_cell_text(i, 2, kor)

    def _add_flow_section(self, flow_text: str):
        """흐름 분석 섹션"""
        self.doc.add_paragraph("■ 흐름 분석 (FLOW)")
        if not flow_text:
            return
        for line in flow_text.split('\n'):
            line = line.strip()
            if line:
                self.doc.add_paragraph(f"  {line}")

    def _add_voca_section(self, data: PassageResult):
        """핵심 어휘 섹션 (3열 테이블)"""
        self.doc.add_paragraph("■ 핵심 어휘 (VOCA)")

        voca_list = data.get_voca_list()
        if not voca_list:
            return

        cols = 3
        rows = (len(voca_list) + cols - 1) // cols
        table = self.doc.add_table(rows=rows, cols=cols)

        for idx, voca in enumerate(voca_list):
            row_idx = idx // cols
            col_idx = idx % cols
            table.set_cell_text(row_idx, col_idx, voca)

    def _add_tf_section(self, tf_text: str, tfa_text: str):
        """T/F 문제 섹션"""
        self.doc.add_paragraph("■ True / False")

        if not tf_text:
            return

        for line in tf_text.split('\n'):
            line = line.strip()
            if line:
                self.doc.add_paragraph(f"  {line}")

        if tfa_text:
            self.doc.add_paragraph(f"  정답: {tfa_text}")

    def _add_summary_section(self, tst_text: str):
        """영어 요약 + 한국어 해석 섹션"""
        self.doc.add_paragraph("■ 요약 (SUMMARY)")

        if not tst_text:
            return

        for line in tst_text.split('\n'):
            line = line.strip()
            if line:
                self.doc.add_paragraph(f"  {line}")

    def build(self) -> bytes:
        """HWPX 파일을 바이트로 반환 (st.download_button 호환)"""
        return self.doc.to_bytes()
