"""DOCX / HWP 파일에서 텍스트를 추출하는 모듈."""
import io
import struct
import zlib


def read_uploaded_file(uploaded_file) -> str:
    """업로드된 파일에서 텍스트를 추출하여 반환.

    지원 형식: .docx, .hwp (HWP5 바이너리), .txt
    """
    name = uploaded_file.name.lower()
    content = uploaded_file.read()

    if name.endswith('.txt'):
        return content.decode('utf-8')
    elif name.endswith('.docx'):
        return _read_docx(content)
    elif name.endswith('.hwp'):
        return _read_hwp(content)
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {name}")


def _read_docx(content: bytes) -> str:
    """python-docx를 사용하여 DOCX 파일에서 텍스트 추출."""
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    return '\n\n'.join(paragraphs)


def _read_hwp(content: bytes) -> str:
    """olefile을 사용하여 HWP5 바이너리 파일에서 텍스트 추출.

    HWP5 형식은 OLE 컨테이너 안에 BodyText/Section{N} 스트림으로 텍스트를 저장한다.
    HWPX(XML 기반) 형식은 지원하지 않는다.
    """
    import olefile

    if not olefile.isOleFile(io.BytesIO(content)):
        raise ValueError(
            "HWP 파일을 읽을 수 없습니다. "
            "HWPX(XML 기반) 형식일 수 있습니다. "
            "한글에서 DOCX로 변환 후 다시 시도해주세요."
        )

    ole = olefile.OleFileIO(io.BytesIO(content))
    try:
        # FileHeader에서 압축 여부 확인
        header = ole.openstream('FileHeader').read()
        is_compressed = (header[36] & 1) != 0

        texts = []
        section_idx = 0
        while ole.exists(f'BodyText/Section{section_idx}'):
            stream_data = ole.openstream(f'BodyText/Section{section_idx}').read()
            if is_compressed:
                try:
                    stream_data = zlib.decompress(stream_data, -15)
                except zlib.error:
                    pass  # 압축 해제 실패 시 원본 데이터 사용

            extracted = _parse_hwp_body_text(stream_data)
            if extracted:
                texts.append(extracted)
            section_idx += 1

        if not texts:
            raise ValueError(
                "HWP 파일에서 텍스트를 추출할 수 없습니다. "
                "한글에서 DOCX로 변환 후 다시 시도해주세요."
            )
        return '\n\n'.join(texts)
    finally:
        ole.close()


def _parse_hwp_body_text(data: bytes) -> str:
    """HWP 본문 레코드에서 텍스트 추출.

    HWPTAG_PARA_TEXT (tag_id=67) 레코드의 UTF-16LE 텍스트를 파싱한다.
    """
    result = []
    pos = 0

    while pos < len(data) - 4:
        header = struct.unpack_from('<I', data, pos)[0]
        tag_id = header & 0x3FF
        size = (header >> 20) & 0xFFF

        if size == 0xFFF:  # 확장 크기
            if pos + 8 > len(data):
                break
            size = struct.unpack_from('<I', data, pos + 4)[0]
            pos += 8
        else:
            pos += 4

        if pos + size > len(data):
            break

        if tag_id == 67:  # HWPTAG_PARA_TEXT
            text_data = data[pos:pos + size]
            chars = []
            i = 0
            while i < len(text_data) - 1:
                char_code = struct.unpack_from('<H', text_data, i)[0]
                if char_code == 13:  # CR → 개행
                    chars.append('\n')
                    i += 2
                elif char_code < 32:
                    # 확장 제어 문자: 16바이트 (코드 1~23, 13 제외)
                    if char_code in range(1, 24) and char_code != 13:
                        i += 16
                    else:
                        i += 2
                else:
                    chars.append(chr(char_code))
                    i += 2

            line = ''.join(chars).strip()
            if line:
                result.append(line)

        pos += size

    return '\n'.join(result)
