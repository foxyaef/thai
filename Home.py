# Home.py 수정 버전

import streamlit as st
import json
from pathlib import Path
from gtts import gTTS
from io import BytesIO

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Thai Vocabulary Learning", layout="wide")
st.title("🇹🇭 태국어 단어 학습")

# ------------------------
# 데이터 불러오기
# ------------------------
def list_sets():
    return sorted([f.stem for f in DATA_DIR.glob("*.json")])

def load_set(name):
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def generate_tts(text, lang="th"):
    mp3 = BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(mp3)
    mp3.seek(0)
    return mp3.read()

sets = list_sets()
selected = st.sidebar.selectbox("단어 세트 선택", sets)

if not selected:
    st.info("관리자 페이지에서 세트를 먼저 만들어주세요.")
    st.stop()

words = load_set(selected)
if not words:
    st.warning("이 세트에는 단어가 없습니다.")
    st.stop()

# ------------------------
# 전체 단어 목록 표시
# ------------------------
st.sidebar.markdown("### 전체 단어 목록")
for i, w in enumerate(words, start=1):
    st.sidebar.write(f"{i}. {w.get('thai','')} - {w.get('meaning_ko','')}")

# ------------------------
# 단어 카드 보기
# ------------------------
st.header(f"📘 세트: {selected}")

# 세션 상태 초기화
if "index" not in st.session_state:
    st.session_state["index"] = 1

# 번호 선택으로 단어 이동
idx = st.number_input(
    "단어 번호 선택",
    min_value=1,
    max_value=len(words),
    value=st.session_state["index"]
)
st.session_state["index"] = idx
item = words[idx-1]

# 카드 표시
col1, col2 = st.columns([2,1])
with col1:
    st.markdown(f"## {item.get('thai','')}")
    st.write(f"**의미(한글):** {item.get('meaning_ko','')}")
    st.write(f"**한국어 발음:** {item.get('pron_kor','')}")
with col2:
    st.markdown("### 발음 듣기")
    audio_bytes = generate_tts(item.get("thai",""))
    st.audio(audio_bytes, format="audio/mp3")
