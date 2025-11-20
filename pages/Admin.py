# pages/Admin.py
import streamlit as st
import json
import os
import pandas as pd
from pathlib import Path
import openai

# 데이터 저장 폴더
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
MAX_WORDS = 100

st.set_page_config(page_title="Admin - Thai Words")

st.title("🛠️ 관리자 페이지")
st.info("단어 묶음 생성 / 수정 / 자동 생성 기능")

# OpenAI 설정
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
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

# ========== 세트 만들기/삭제 ==========
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

# ========== GPT 자동 생성 ==========
st.subheader("🤖 GPT 자동 단어 생성")

autoname = st.text_input("생성할 세트 이름")
num = st.slider("단어 수", 10, 100, 100)

if st.button("GPT 자동 생성 시작"):
    if not OPENAI_API_KEY:
        st.error("OpenAI API 키가 필요합니다")
        st.stop()

    prompt = f"""
너는 태국어 단어를 JSON 형식으로 생성하는 도우미야.
아래 형식의 객체 100개를 JSON 배열로 반환해줘.

[
  {{
    "thai": "단어",
    "transliteration": "로마자",
    "pron_kor": "한국어근사발음",
    "pos": "품사",
    "meaning_ko": "뜻",
    "example_th": "예문",
    "example_ko": "예문번역"
  }},
  ...
]

설명 없이 JSON 배열만 반환해줘.
"""

    with st.spinner("GPT가 단어 생성 중..."):
        res = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            max_tokens=2500,
            temperature=0.7
        )

    text = res.choices[0].message.content
    try:
        data = json.loads(text)
        data = data[:num]
        save_set(autoname, data)
        st.success(f"세트 '{autoname}' 생성 완료 ({len(data)}개)")
    except:
        st.error("GPT 출력 파싱 실패")
        st.code(text)

st.markdown("---")

# ========== 수동 편집 ==========
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
