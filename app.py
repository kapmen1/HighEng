import json

import streamlit as st

from config import MODEL_CATALOG, get_model_labels, get_model_info
from llm import create_llm
from document.schema import PassageResult
from document.docx_builder import DocxBuilder
from utils.text_processing import split_sentences, split_passages

# 페이지 설정
st.set_page_config(
    page_title="HighEng - 영어 지문 학습 도우미",
    page_icon="📚",
    layout="wide",
)


# ─── 헬퍼 함수 ────────────────────────────────────
def _generate_passage_no(starting_no: str, index: int) -> str:
    """시작 번호와 인덱스로 지문 번호 생성.

    예: '9-1' + index 2 → '9-3', '1' + index 2 → '3'
    """
    if '-' in starting_no:
        prefix, suffix = starting_no.rsplit('-', 1)
        try:
            return f"{prefix}-{int(suffix) + index}"
        except ValueError:
            return f"{starting_no}_{index + 1}"
    else:
        try:
            return str(int(starting_no) + index)
        except ValueError:
            return f"{starting_no}_{index + 1}"


def _display_single_result(result: PassageResult):
    """단일 지문 분석 결과를 탭으로 표시."""
    d = result.to_dict()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📝 번역", "📖 키워드", "✅ T/F 문제", "📋 요약", "🔧 JSON"]
    )

    # --- 번역 탭 ---
    with tab1:
        eng_sentences = split_sentences(d.get('Eng', ''))
        kor_sentences = split_sentences(d.get('Kor', ''))
        row_count = max(len(eng_sentences), len(kor_sentences))

        if row_count > 0:
            table_data = []
            for i in range(row_count):
                eng = eng_sentences[i] if i < len(eng_sentences) else ""
                kor = kor_sentences[i] if i < len(kor_sentences) else ""
                table_data.append({"#": i + 1, "English": eng, "한국어": kor})
            st.table(table_data)
        else:
            st.info("번역 결과가 없습니다.")

    # --- 키워드 탭 ---
    with tab2:
        voca_list = result.get_voca_list()
        if voca_list:
            voca_data = []
            for v in voca_list:
                parts = v.split(' ', 1)
                if len(parts) == 2:
                    voca_data.append({"영단어": parts[0], "뜻": parts[1]})
                else:
                    voca_data.append({"영단어": v, "뜻": ""})
            st.table(voca_data)
        else:
            st.info("키워드가 없습니다.")

    # --- T/F 탭 ---
    with tab3:
        tf_text = d.get('TF', '')
        if tf_text:
            for line in tf_text.split('\n'):
                line = line.strip()
                if line:
                    st.markdown(f"- {line}")

            with st.expander("정답 보기"):
                tfa = d.get('TFA', '')
                st.markdown(f"**{tfa}**")
        else:
            st.info("T/F 문제가 없습니다.")

    # --- 요약 탭 ---
    with tab4:
        tst_text = d.get('TST', '')
        if tst_text:
            lines = tst_text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    if i == 0:
                        st.markdown(f"**[영어 요약]**\n\n{line}")
                    else:
                        st.markdown(f"**[한국어 해석]**\n\n{line}")
        else:
            st.info("요약이 없습니다.")

        flow_text = d.get('Flow', '')
        if flow_text:
            st.divider()
            st.markdown("**[흐름 분석]**")
            for line in flow_text.split('\n'):
                line = line.strip()
                if line:
                    st.markdown(f"- {line}")

    # --- JSON 탭 ---
    with tab5:
        st.json(d)


# ─── 사이드바 ───────────────────────────────────────
with st.sidebar:
    st.header("설정")

    # 모델군 선택
    provider = st.selectbox(
        "LLM 공급자 선택",
        list(MODEL_CATALOG.keys()),
        index=0,
    )

    # 세부 모델 선택
    sub_labels = get_model_labels(provider)
    sub_model_label = st.selectbox("모델 선택", sub_labels, index=0)
    model_info = get_model_info(provider, sub_model_label)

    # 성능 및 가격 안내
    tier = model_info["tier"]
    tier_label = {"하": "낮은 성능", "중": "중간 성능", "상": "높은 성능"}[tier]
    st.info(
        f"**{tier_label}** · _{model_info['note']}_\n\n"
        f"입력 \\${model_info['input_price']:.2f} / 출력 \\${model_info['output_price']:.2f} (1M 토큰당)\n\n"
        f"_실제 비용은 분석 후 표시됩니다_"
    )

    st.divider()

    # API Key 입력
    api_key = st.text_input(
        f"{provider} API Key",
        type="password",
        placeholder="API Key를 입력하세요",
    )

    # API Key 발급 안내
    with st.expander("API Key 발급 안내"):
        if provider == "Gemini":
            st.markdown("""
**Google Gemini API Key 발급 방법**
1. [Google AI Studio](https://aistudio.google.com/) 접속
2. Google 계정으로 로그인
3. 좌측 메뉴에서 **Get API Key** 클릭
4. **Create API Key** 버튼 클릭
5. 생성된 키를 복사하여 위에 붙여넣기
            """)
        elif provider == "Claude":
            st.markdown("""
**Anthropic Claude API Key 발급 방법**
1. [Anthropic Console](https://console.anthropic.com/) 접속
2. 계정 생성 또는 로그인
3. 좌측 메뉴에서 **API Keys** 클릭
4. **Create Key** 버튼 클릭
5. 생성된 키를 복사하여 위에 붙여넣기
            """)
        elif provider == "ChatGPT":
            st.markdown("""
**OpenAI ChatGPT API Key 발급 방법**
1. [OpenAI Platform](https://platform.openai.com/) 접속
2. 계정 생성 또는 로그인
3. 우측 상단 프로필 > **API Keys** 클릭
4. **Create new secret key** 버튼 클릭
5. 생성된 키를 복사하여 위에 붙여넣기
            """)

    st.divider()
    st.caption("HighEng v1.1 | 영어 지문 학습 도우미")


# ─── 메인 영역 ──────────────────────────────────────
st.title("📚 HighEng")
st.markdown("영어 지문을 입력하면 **번역, 키워드, T/F 문제, 요약**을 자동으로 생성합니다.")

# ─── 입력 방식 선택 ────────────────────────────────
input_method = st.radio(
    "입력 방식",
    ["직접 입력", "파일 업로드"],
    horizontal=True,
)

if input_method == "파일 업로드":
    uploaded_file = st.file_uploader(
        "DOCX / HWP / TXT 파일 업로드",
        type=["docx", "hwp", "txt"],
        help="Word(.docx), 한글(.hwp), 텍스트(.txt) 파일을 업로드하세요.",
    )
    if uploaded_file is not None:
        try:
            from utils.file_reader import read_uploaded_file
            extracted_text = read_uploaded_file(uploaded_file)
            st.session_state.uploaded_text = extracted_text
            st.success(f"파일에서 텍스트를 추출했습니다. ({len(extracted_text)}자)")
        except Exception as e:
            st.error(f"파일 읽기 실패: {e}")
            extracted_text = ""
    else:
        extracted_text = st.session_state.get("uploaded_text", "")

    default_text = extracted_text
else:
    default_text = ""

# ─── 지문 입력 영역 ────────────────────────────────
col_input, col_config = st.columns([5, 1])
with col_input:
    english_text = st.text_area(
        "영어 지문 입력 (여러 지문은 번호 매기기 또는 빈 줄 2개로 구분)",
        value=default_text,
        height=300,
        placeholder="1. First passage text...\n\n\n2. Second passage text...",
    )
with col_config:
    # 자동 감지된 지문 수를 기본값으로 사용
    if english_text.strip():
        auto_detected = split_passages(english_text.strip())
        suggested_count = len(auto_detected)
    else:
        suggested_count = 1

    passage_count = st.number_input(
        "지문 수", min_value=1, max_value=20,
        value=suggested_count, step=1,
    )
    starting_no = st.text_input(
        "시작 번호",
        value="1",
        placeholder="예: 9-1",
    )

# 지문 수 불일치 경고
if english_text.strip():
    detected_passages = split_passages(english_text.strip())
    detected_count = len(detected_passages)
    if detected_count != passage_count:
        st.warning(
            f"⚠️ 입력에서 {detected_count}개 지문이 감지되었으나, "
            f"설정된 지문 수는 {passage_count}개입니다. 지문 수를 확인해주세요."
        )

# 분석 시작 버튼
submit = st.button("🔍 분석 시작", type="primary", use_container_width=True)

# ─── 분석 실행 ──────────────────────────────────────
if submit:
    # 입력 검증
    if not api_key:
        st.error("사이드바에서 API Key를 입력해주세요.")
        st.stop()
    if not english_text.strip():
        st.error("영어 지문을 입력해주세요.")
        st.stop()

    passages = split_passages(english_text.strip())
    if not passages:
        st.error("지문을 입력해주세요.")
        st.stop()

    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, passage_text in enumerate(passages):
        p_no = _generate_passage_no(starting_no.strip(), i)
        status_text.text(f"[{i + 1}/{len(passages)}] 지문 {p_no} 분석 중... ({provider} {sub_model_label})")
        progress_bar.progress((i + 1) / len(passages))

        try:
            llm = create_llm(provider, api_key, model_info["model_id"])
            result = llm.analyze_passage(passage_text, p_no)
            # 실제 토큰 사용량으로 비용 계산
            usage = llm.last_usage
            cost = (usage["input_tokens"] * model_info["input_price"]
                    + usage["output_tokens"] * model_info["output_price"]) / 1_000_000
            results.append({"result": result, "cost": cost, "usage": usage})
        except ValueError as e:
            st.error(f"지문 {p_no} 응답 파싱 실패: {e}")
            results.append(None)
        except Exception as e:
            err_msg = str(e).lower()
            if "api_key" in err_msg or "authentication" in err_msg or "invalid" in err_msg:
                st.error("API Key가 올바르지 않습니다. 사이드바에서 키를 확인해주세요.")
                st.stop()
            elif "rate" in err_msg or "quota" in err_msg:
                st.warning(f"지문 {p_no}: API 호출 한도에 도달했습니다. 잠시 후 다시 시도해주세요.")
                results.append(None)
            else:
                st.error(f"지문 {p_no} 오류: {e}")
                results.append(None)

    progress_bar.empty()
    status_text.empty()

    st.session_state.results = results
    success_entries = [r for r in results if r is not None]
    total_cost = sum(r["cost"] for r in success_entries)
    total_input = sum(r["usage"]["input_tokens"] for r in success_entries)
    total_output = sum(r["usage"]["output_tokens"] for r in success_entries)
    st.session_state.total_cost = total_cost

    if success_entries:
        st.success(
            f"분석 완료! ({len(success_entries)}/{len(passages)}개 성공)\n\n"
            f"💰 실제 비용: **\\${total_cost:.4f}** "
            f"(입력 {total_input:,}토큰 + 출력 {total_output:,}토큰)"
        )
    else:
        st.error("모든 지문 분석에 실패했습니다.")

# ─── 결과 표시 ──────────────────────────────────────
if "results" in st.session_state:
    raw_results = st.session_state.results
    valid_entries = [(i, r) for i, r in enumerate(raw_results) if r is not None]

    if not valid_entries:
        pass  # 유효한 결과 없음
    elif len(valid_entries) == 1:
        # 단일 지문: 기존 레이아웃 유지
        entry = valid_entries[0][1]
        result = entry["result"]
        d = result.to_dict()
        st.divider()
        st.subheader(f"📄 [{d.get('No', '')}] {d.get('Topic', '')}")
        st.caption(f"💰 비용: \\${entry['cost']:.4f} (입력 {entry['usage']['input_tokens']:,} + 출력 {entry['usage']['output_tokens']:,} 토큰)")
        _display_single_result(result)
    else:
        # 다중 지문: expander로 감싸기
        st.divider()
        st.subheader(f"📄 분석 결과 ({len(valid_entries)}개 지문)")
        for idx, entry in valid_entries:
            result = entry["result"]
            d = result.to_dict()
            with st.expander(
                f"[{d.get('No', '')}] {d.get('Topic', '')}  —  \\${entry['cost']:.4f}",
                expanded=(idx == 0),
            ):
                _display_single_result(result)

    # ─── 다운로드 ──────────────────────────────────
    if valid_entries:
        st.divider()
        st.subheader("📥 파일 다운로드")

        # 총 실제 비용 표시
        if "total_cost" in st.session_state:
            st.caption(f"💰 총 실제 비용: **\\${st.session_state.total_cost:.4f}**")

        col_dl1, col_dl2 = st.columns(2)

        with col_dl1:
            try:
                builder = DocxBuilder()
                for _, entry in valid_entries:
                    builder.add_passage(entry["result"])
                docx_bytes = builder.build()

                if len(valid_entries) == 1:
                    d = valid_entries[0][1]["result"].to_dict()
                    filename = f"HighEng_결과_{d.get('No', 'result')}.docx"
                else:
                    filename = "HighEng_결과_전체.docx"

                st.download_button(
                    label="📄 DOCX 다운로드",
                    data=docx_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"DOCX 생성 실패: {e}")

        with col_dl2:
            if len(valid_entries) == 1:
                d = valid_entries[0][1]["result"].to_dict()
                json_data = d
                filename_json = f"HighEng_결과_{d.get('No', 'result')}.json"
            else:
                json_data = [e["result"].to_dict() for _, e in valid_entries]
                filename_json = "HighEng_결과_전체.json"

            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="🔧 JSON 다운로드",
                data=json_str,
                file_name=filename_json,
                mime="application/json",
                use_container_width=True,
            )

        # 다운로드 안내 (수정 4)
        st.caption(
            "💡 **다운로드 위치 설정 안내**: 브라우저 설정에서 "
            "'다운로드 전에 각 파일의 저장 위치 확인'을 활성화하면 "
            "원하는 폴더에 직접 저장할 수 있습니다.\n\n"
            "- **Chrome**: 설정 → 다운로드 → '다운로드 전에 각 파일의 저장 위치 확인'\n"
            "- **Edge**: 설정 → 다운로드 → '다운로드할 때마다 수행할 작업 묻기'"
        )
