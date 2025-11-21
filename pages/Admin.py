# pages/Admin.py
import streamlit as st
import json
import os
import pandas as pd
from pathlib import Path
from openai import OpenAI

ADMIN_PASSWORD = "thaivocas"  # 원하는 비밀번호로 변경

# 세션 상태 초기화
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# 로그인 시도
if not st.session_state.admin_authenticated:
    st.warning("이 페이지는 관리자 전용입니다.\nAPI 비용 때문에 접근을 제한합니다. 죄송합니다 ㅎㅎ")
    password_input = st.text_input("관리자 비밀번호 입력", type="password")
    if st.button("로그인"):
        if password_input == ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            st.success("✅ 로그인 성공!")
            st.experimental_rerun()  # 페이지 새로고침
        else:
            st.error("❌ 비밀번호가 틀렸습니다.")
    st.stop()  # 비밀번호가 맞지 않으면 아래 코드 실행 중단


# 데이터 저장 폴더
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MAX_WORDS = 100

st.set_page_config(page_title="Admin - Thai Words")

st.title("🛠️ 관리자 페이지")
st.info("단어 묶음 생성 / 수정 / 자동 생성 기능")

# OpenAI 설정
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)
MODEL = "gpt-4o-mini"


# UTILS
def list_sets():
    return sorted([f.stem for f in DATA_DIR.glob("*.json")])

def load_set(name):
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def save_set(name, data):
    path = DATA_DIR / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def delete_set(name):
    (DATA_DIR / f"{name}.json").unlink()


# --------------------------
# ▣ 세트 생성/삭제
# --------------------------
st.subheader("📁 세트 관리")

c1, c2 = st.columns(2)

with c1:
    new_name = st.text_input("새 세트 이름")
    if st.button("세트 생성"):
        if not new_name:
            st.error("세트 이름을 입력하세요.")
        else:
            save_set(new_name, [])
            st.success(f"'{new_name}' 세트 생성 완료")
            st.experimental_rerun()

with c2:
    existing = list_sets()
    delete_target = st.selectbox("삭제할 세트 선택", existing)
    if st.button("세트 삭제"):
        delete_set(delete_target)
        st.success("삭제 완료")
        st.experimental_rerun()


st.markdown("---")


# --------------------------
# ▣ GPT 자동 생성
# --------------------------
st.subheader("🤖 GPT 자동 단어 생성")

autoname = st.text_input("생성할 세트 이름")
num = st.slider("단어 수", 10, 50, 50)

if st.button("GPT 자동 생성 시작"):
    if not api_key:
        st.error("OpenAI API 키가 필요합니다")
        st.stop()

    # ▣ 기존 세트의 모든 태국어 단어 수집
    all_existing = []
    for set_name in list_sets():
        data = load_set(set_name)
        for item in data:
            if "thai" in item:
                all_existing.append(item["thai"])

    existing_list_text = json.dumps(all_existing, ensure_ascii=False)

    # 🔥 GPT 프롬프트
    prompt = f"""
너는 태국어 단어를 JSON 형식으로 생성하는 도우미야.

이미 존재하는 태국어 단어 목록은 다음과 같아:
{existing_list_text}

⚠️ 중요한 규칙:
- 위 목록에 포함된 단어는 절대로 생성하지 마라.
- 기존 단어와 철자가 같은 단어도 생성 금지.

{num}개의 새로운 태국어 단어를 아래 형식으로 JSON 배열로 출력해줘:

[
  {{
    "thai": "단어",
    "pron_kor": "한국어발음표기",
    "meaning_ko": "뜻",
  }}
]

조건:
- 학교에서 자주 쓰는 단어
- 10대 학생들의 일상 대화에 쓰는 단어
- 태국 여행 시 유용한 단어
을 섞어서 생성해줘.

설명 없이 JSON 배열만 정확히 반환해줘.
"""

    # === GPT 호출 ===
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "당신은 태국어 단어 생성기입니다."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7
    )

    result_text = response.choices[0].message.content
    print(result_text)

    st.code(result_text)

    # === JSON 파싱 ===
    try:
        data = json.loads(result_text)

        # 혹시라도 GPT가 중복 단어를 넣었을 때 필터링
        filtered = [item for item in data if item["thai"] not in all_existing]
        filtered = filtered[:num]

        save_set(autoname, filtered)
        st.success(f"세트 '{autoname}' 생성 완료 ({len(filtered)}개)")

    except Exception as e:
        st.error("❌ GPT 출력 JSON 파싱 실패")
        st.code(result_text)
        st.error(str(e))



# --------------------------
# ▣ 수동 편집
# --------------------------
st.subheader("✍️ 단어 수동 편집")

sets = list_sets()
target = st.selectbox("편집할 세트 선택", sets)

rows = load_set(target)
df = pd.DataFrame(rows)

edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)

if st.button("저장"):
    save_set(target, edited.to_dict(orient="records"))
    st.success("저장 완료")

# JSON 업로드
upload = st.file_uploader("JSON 세트 업로드", type=["json"])
if upload:
    try:
        data = json.load(upload)
        save_set(target, data)
        st.success("업로드 완료")
    except:
        st.error("JSON 파싱 실패")
