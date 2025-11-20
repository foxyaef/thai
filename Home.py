# Home.py
import streamlit as st
import json
import os
from pathlib import Path
from gtts import gTTS
from io import BytesIO

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Thai Vocabulary Learning", layout="wide")
st.title("🇹🇭 태국어 단어 학습")

# Load sets
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

st.header(f"📘 세트: {selected}")

# 카드식 단어 보기
idx = st.number_input("단어 번호", min_value=1, max_value=len(words), value=1)
item = words[idx-1]

col1, col2 = st.columns([2,1])
with col1:
    st.markdown(f"## {item.get('thai','')}")
    st.write(f"**의미(한글):** {item.get('meaning_ko','')}")
    st.write(f"**품사:** {item.get('pos','')}")
    st.write(f"**로마자:** {item.get('transliteration','')}")
    st.write(f"**한국어 발음:** {item.get('pron_kor','')}")

    st.markdown("**예문(Thai)**")
    st.write(item.get("example_th",""))
    st.markdown("**예문(Korean)**")
    st.write(item.get("example_ko",""))

with col2:
    st.markdown("### 발음 듣기")
    audio_bytes = generate_tts(item.get("thai",""))
    st.audio(audio_bytes, format="audio/mp3")

# 이전/다음 버튼
c1, c2, c3 = st.columns(3)
if c1.button("◀ 이전"):
    st.session_state["index"] = max(1, idx-1)
    st.experimental_rerun()
if c3.button("다음 ▶"):
    st.session_state["index"] = min(len(words), idx+1)
    st.experimental_rerun()
