import os
import time
import traceback
import streamlit as st
import google.generativeai as genai

# ------------- Konfigurasi UI -------------
st.set_page_config(page_title="Gemini Catbot", page_icon="🐱", layout="wide")

# Personas: Perintah terhadap persona yang dipilih
PERSONAS = {
    "Ahli Kucing": (
        "Kamu ahli kucing yang merangkum dokter hewan, ahli nutrisi, dan pelatih perilaku. "
        "Utamakan keselamatan, nutrisi yang aman, dan modifikasi perilaku yang positif. "
        "Beri langkah praktis. Jika ada gejala berat, sarankan kunjungan ke dokter hewan."
    ),
    "Ahli Strategi Bisnis": (
        "Kamu konsultan strategi. Analisis pasar, positioning, dan model bisnis. "
        "Buat rencana eksekusi 30-60-90 hari. Gunakan kerangka seperti SWOT, 7P, dan JTBD bila relevan. "
        "Fokus pada prioritas berdampak besar."
    ),
    "Ahli Periklanan": (
        "Kamu creative director periklanan. Tulis konsep kampanye, headline, copy, CTA, dan variasi angle. "
        "Gunakan AIDA dan usulkan eksperimen cepat lintas channel."
    ),
    "Ahli Gizi dan Nutrisi": (
        "Kamu ahli gizi. Berikan saran diet untuk manusia yang aman dan seimbang, bukan diagnosis. "
        "Jika perlu, sarankan konsultasi profesional. Sertakan estimasi makro dan tips praktis."
    ),
    "Ahli Manajemen Proyek": (
        "Kamu manajer proyek. Susun WBS, timeline, risiko, dan RACI. "
        "Gunakan checklist, milestone, dan komunikasi yang jelas."
    ),
    "Analis Data": (
        "Kamu analis data. Bantu rumuskan hipotesis, metrik, eksperimen A/B, dan interpretasi hasil. "
        "Berikan contoh kueri SQL jika relevan."
    ),
    "Growth Marketer": (
        "Kamu growth marketer. Fokus pada funnel AARRR, ide eksperimen cepat, dan prioritas berbasis ICE score."
    ),
    "Ahli UX Research": (
        "Kamu peneliti UX. Sarankan metode riset, pedoman interview, persona pengguna, dan sintesis temuan."
    ),
    "Manajer Produk": (
        "Kamu manajer produk. Klarifikasi masalah, tetapkan ruang lingkup, acceptance criteria, dan roadmap singkat."
    ),
    "Arsitek Perangkat Lunak": (
        "Kamu arsitek perangkat lunak. Usulkan arsitektur yang sederhana, jelaskan trade-off, dan langkah implementasi bertahap."
    ),
    "Asisten Umum": (
        "Kamu adalah asisten umum yang sopan. Jawab to the point dan sertakan langkah jelas jika relevan."
    ),
}

DEFAULT_MODEL = "gemini-1.5-flash"

# ------------- PENCATATAN SESI -------------
if "connected" not in st.session_state:
    st.session_state.connected = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "persona" not in st.session_state:
    st.session_state.persona = "Asisten Umum"
if "model_name" not in st.session_state:
    st.session_state.model_name = DEFAULT_MODEL
if "chat" not in st.session_state:
    st.session_state.chat = None
if "history" not in st.session_state:
    st.session_state.history = []  # List {role, content}
# Perhitungan TOKEN Per API (Untuk GEMINI)
if "usage" not in st.session_state:
    st.session_state.usage = {
        "gemini": {
            "requests": 0,
            "prompt_tokens": 0,
            "candidate_tokens": 0,
            "total_tokens": 0,
        }
    }

# ------------- HELPERS: Fallback, Logika penanganan kesalahan minor, Pembaruan pada UI dari respon chat -------------

def reset_chat():
    st.session_state.history = []
    st.session_state.chat = None


def connect_gemini(api_key: str) -> tuple[bool, str]:
    """Try to configure the SDK and make a tiny request to verify the key."""
    try:
        if not api_key:
            return False, "API key kosong"
        genai.configure(api_key=api_key)
        # build a tiny model and issue a very short call
        model = genai.GenerativeModel(st.session_state.model_name, system_instruction=PERSONAS[st.session_state.persona])
        # Very short prompt to minimize token usage
        resp = model.generate_content("ping")
        # If we get here without exception, consider connected
        # Update usage metrics, if available
        um = getattr(resp, "usage_metadata", None)
        if um:
            st.session_state.usage["gemini"]["requests"] += 1
            st.session_state.usage["gemini"]["prompt_tokens"] += getattr(um, "prompt_token_count", 0) or 0
            st.session_state.usage["gemini"]["candidate_tokens"] += getattr(um, "candidates_token_count", 0) or 0
            st.session_state.usage["gemini"]["total_tokens"] += getattr(um, "total_token_count", 0) or 0
        return True, "Terhubung"
    except Exception as e:
        return False, f"Gagal menghubungkan: {e}"


def ensure_chat() -> genai.ChatSession:
    if st.session_state.chat is None:
        model = genai.GenerativeModel(
            st.session_state.model_name,
            system_instruction=PERSONAS[st.session_state.persona],
        )
        # Convert history to Gemini format
        hist = []
        for m in st.session_state.history:
            role = "user" if m["role"] == "user" else "model"
            hist.append({"role": role, "parts": [m["content"]]})
        st.session_state.chat = model.start_chat(history=hist)
    return st.session_state.chat


def send_message(user_text: str) -> str:
    chat = ensure_chat()
    resp = chat.send_message(user_text)
    # Update usage counters
    um = getattr(resp, "usage_metadata", None)
    if um:
        st.session_state.usage["gemini"]["requests"] += 1
        st.session_state.usage["gemini"]["prompt_tokens"] += getattr(um, "prompt_token_count", 0) or 0
        st.session_state.usage["gemini"]["candidate_tokens"] += getattr(um, "candidates_token_count", 0) or 0
        st.session_state.usage["gemini"]["total_tokens"] += getattr(um, "total_token_count", 0) or 0
    return resp.text

# ------------- SIDEBAR -------------
with st.sidebar:
    st.header("Pengaturan")
    # API key input
    api_key_input = st.text_input("Masukkan Gemini API Key", value=st.session_state.api_key, type="password", help="Key dari makersuite.google.com atau Google AI Studio")
    model_name = st.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-flash-8b"], index=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-flash-8b"].index(st.session_state.model_name))
    persona = st.selectbox("Persona", list(PERSONAS.keys()), index=list(PERSONAS.keys()).index(st.session_state.persona))
    temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
    colA, colB = st.columns(2)
    with colA:
        if st.button("Hubungkan / Ganti API Key", use_container_width=True):
            st.session_state.api_key = api_key_input
            st.session_state.model_name = model_name
            st.session_state.persona = persona
            reset_chat()
            ok, msg = connect_gemini(st.session_state.api_key)
            st.session_state.connected = ok
            if ok:
                st.session_state.connect_msg = msg
            else:
                st.session_state.connect_msg = msg
    with colB:
        if st.button("Reset Sesi", use_container_width=True):
            reset_chat()
            st.toast("Sesi direset")

    # Connection status text
    if st.session_state.connected:
        st.markdown("<span style='color: #16a34a; font-size: 0.85rem;'>API berhasil terhubung</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color: #ef4444; font-size: 0.85rem;'>Belum terhubung</span>", unsafe_allow_html=True)

    # Usage metrics
    st.subheader("Statistik Pemakaian")
    u = st.session_state.usage["gemini"]
    st.metric("Requests", u["requests"]) 
    st.metric("Prompt Tokens", u["prompt_tokens"]) 
    st.metric("Candidate Tokens", u["candidate_tokens"]) 
    st.metric("Total Tokens", u["total_tokens"]) 

# ------------- MAIN -------------
st.title("🐱 Gemini Catbot")
st.caption("Pilih persona, masukkan API key, lalu mulai chat.")

# Show persona description
with st.expander("Deskripsi persona", expanded=False):
    st.write(PERSONAS[st.session_state.persona])

# Chat history rendering
for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"]) 

# Input box
user_msg = st.chat_input("Tanya sesuatu tentang kucing atau apa pun...")

if user_msg:
    if not st.session_state.connected:
        st.warning("Masukkan dan hubungkan API key dulu di sidebar.")
    else:
        st.session_state.history.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                reply = send_message(user_msg)
                placeholder.markdown(reply)
                st.session_state.history.append({"role": "assistant", "content": reply})
            except Exception as e:
                placeholder.error(f"Terjadi kesalahan: {e}")
                st.exception(e)

# Footer small help
st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown(
    "<div style='font-size:0.85rem; color:#6b7280;'>Tip: ganti persona di sidebar untuk gaya jawaban berbeda. Token dihitung otomatis dari usage metadata API.</div>",
    unsafe_allow_html=True,
)
