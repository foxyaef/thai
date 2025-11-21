# pages/Admin.py
import streamlit as st
import json
import os
import pandas as pd
from pathlib import Path
from openai import OpenAI
import re

# --------------------------
# 데이터 저장 폴더
# --------------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MAX_WORDS = 100

st.set_page_config(page_title="Admin - Thai Words")
st.title("🛠️ 관리자 페이지")
st.info("단어 묶음 생성 / 수정 / 자동 생성 기능")

# --------------------------
# OpenAI 설정
# --------------------------
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)
MODEL = "gpt-4o-mini"

# --------------------------
# UTILS
# --------------------------
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
    path = DATA_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
    else:
        st.warning(f"'{name}.json' 파일이 존재하지 않아 삭제할 수 없습니다.")

def safe_load_words(result_text):
    """
    GPT 출력에서 JSON 배열을 개별 항목으로 파싱,
    형식 오류 단어는 제외
    """
    try:
        data = json.loads(result_text)
        if isinstance(data, list):
            valid_items = []
            for item in data:
                if isinstance(item, dict) and "thai" in item:
                    valid_items.append(item)
            return valid_items
    except Exception:
        pass  # 전체 배열 파싱 실패 시 아래 정규식 시도

    # {} 단위로 개별 파싱
    items = re.findall(r"\{.*?\}", result_text, re.DOTALL)
    valid_items = []
    for it in items:
        try:
            obj = json.loads(it)
            if "thai" in obj:
                valid_items.append(obj)
        except Exception:
            continue
    return valid_items

def get_auto_set_name():
    """
    자동 단어장 이름 생성: '01', '02', ...
    """
    existing = list_sets()
    n = 1
    while True:
        name = f"{n:02d}"
        if name not in existing:
            return name
        n += 1

# --------------------------
# ▣ 세트 생성/삭제
# --------------------------
st.subheader("📁 세트 관리")
c1, c2 = st.columns(2)

with c1:
    auto_name = get_auto_set_name()
    new_name = st.text_input("새 세트 이름", value=auto_name)
    if st.button("세트 생성"):
        if not new_name:
            st.error("세트 이름을 입력하세요.")
        else:
            # 빈 리스트 대신 기본 항목 1개 포함
            default_item = {"thai": "", "pron_kor": "", "meaning_ko": ""}
            save_set(new_name, [default_item])
            st.success(f"'{new_name}' 세트 생성 완료")
            st.experimental_rerun()


with c2:
    existing = list_sets()
    if existing:
        delete_target = st.selectbox("삭제할 세트 선택", existing)
        if st.button("세트 삭제"):
            delete_set(delete_target)
            st.success("삭제 완료")
            st.experimental_rerun()
    else:
        st.info("삭제할 세트가 없습니다.")

st.markdown("---")

# --------------------------
# ▣ GPT 자동 생성
# --------------------------
st.subheader("🤖 GPT 자동 단어 생성")

autoname = st.text_input("생성할 세트 이름 (자동 생성 가능)", value=get_auto_set_name())
num = st.slider("단어 수", 10, 50, 50)

if st.button("GPT 자동 생성 시작"):
    if not api_key:
        st.error("OpenAI API 키가 필요합니다")
        st.stop()

    # 기존 단어 수집
    all_existing = []
    for set_name in list_sets():
        data = load_set(set_name)
        for item in data:
            if "thai" in item:
                all_existing.append(item["thai"])
    existing_list_text = json.dumps(all_existing, ensure_ascii=False)

    # GPT 프롬프트
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
    "meaning_ko": "뜻"
  }}
]

조건:
- 학교에서 자주 쓰는 단어
- 10대 학생들의 일상 대화에 쓰는 단어
- 태국 여행 시 유용한 단어
을 섞어서 생성해줘.

반드시 JSON 배열만 반환하고, 설명이나 코드 블록 없이 출력해줘.
"""

    # GPT 호출
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "당신은 태국어 단어 생성기입니다."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7
    )

    result_text = response.choices[0].message.content
    st.code(result_text)

    # JSON 안전 파싱
    data = safe_load_words(result_text)

    # 중복 단어 제거
    filtered = [item for item in data if item["thai"] not in all_existing]
    filtered = filtered[:num]

    save_set(autoname, filtered)
    st.success(f"세트 '{autoname}' 생성 완료 ({len(filtered)}개)")

st.markdown("---")

# --------------------------
# ▣ 수동 편집
# --------------------------
st.subheader("✍️ 단어 수동 편집")

sets = list_sets()
if sets:
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
else:
    st.info("편집할 세트가 없습니다.")
