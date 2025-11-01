import streamlit as st
from home import home
from price_dashboard import price_dashboard
import price_tracking
from tracklist import show_tracklist
from market_locator import show_market_locator
from session_utils import load_tracklist, save_tracklist

# ------------------ THEME LOADER ------------------
def load_theme():
    try:
        with open("theme.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Theme not loaded: {e}")
# ---------------------------------------------------

# 🌍 languages are already in app.py (your previous message)
LANGUAGES = {
    "en": "English",
    "hi": "हिंदी",
    "mr": "मराठी",
    "gu": "ગુજરાતી",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "bn": "বাংলা",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
    "pa": "ਪੰਜਾਬੀ",
    "ur": "اُردُو"
}

st.set_page_config(page_title="Kisan App", page_icon="🌾", layout="wide")
load_theme()   # 👈 important: load once, top-level

# ---------- tracklist persistence ----------
if "tracklist" not in st.session_state:
    st.session_state.tracklist = load_tracklist()
else:
    save_tracklist(st.session_state.tracklist)

# ---------- language persistence ----------
if "lang" not in st.session_state:
    st.session_state.lang = "en"

with st.sidebar:
    st.markdown("### 🌐 Select Language / भाषा चुनें")
    selected_lang = st.radio(
        "Choose Language",
        list(LANGUAGES.values()),
        index=list(LANGUAGES.keys()).index(st.session_state.lang)
    , key="lang_radio")
    st.session_state.lang = [k for k, v in LANGUAGES.items() if v == selected_lang][0]

# ---------- navigation from query params ----------
query_params = st.query_params
page_param = query_params.get("page", ["home"])
current_page = page_param[0] if isinstance(page_param, list) else page_param

if "page" not in st.session_state:
    st.session_state["page"] = current_page
elif st.session_state["page"] != current_page:
    st.session_state["page"] = current_page
    st.rerun()

page = st.session_state["page"]

if page == "home":
    home()
elif page == "tracklist":
    show_tracklist()
elif page == "locator":
    show_market_locator()
elif page == "tracking":
    price_tracking.price_tracking()
elif page == "dashboard":
    price_dashboard()

# ---------- bottom nav ----------
st.markdown("""
<div class="bottom-nav">
    <a href="?page=home" class="nav-item"><span class="nav-icon">🏠</span>Home</a>
    <a href="?page=tracklist" class="nav-item"><span class="nav-icon">📋</span>Tracklist</a>
    <a href="?page=locator" class="nav-item"><span class="nav-icon">📍</span>Locator</a>
</div>
""", unsafe_allow_html=True)
