import streamlit as st
import pandas as pd
import requests
import json
from pathlib import Path
from translator import t

# --- Load Theme ---
def load_theme():
    try:
        with open("theme.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

load_theme()

TRACKLIST_FILE = Path("tracklist_data.json")

# --- Helpers to save/load JSON ---
def load_tracklist():
    if TRACKLIST_FILE.exists():
        try:
            with open(TRACKLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_tracklist(data):
    with open(TRACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# --- Crop List ---
CROP_LIST = sorted([
    "Wheat", "Rice", "Maize", "Barley", "Bajra", "Jowar", "Ragi",
    "Paddy", "Cotton", "Groundnut", "Soyabean", "Sunflower", "Sesamum",
    "Mustard", "Gram", "Tur", "Urad", "Moong", "Masoor", "Onion",
    "Potato", "Tomato", "Cabbage", "Cauliflower", "Brinjal", "Chilli",
    "Garlic", "Ginger", "Sugarcane", "Banana", "Apple", "Mango",
    "Grapes", "Guava", "Papaya", "Orange", "Pomegranate", "Peas",
    "Turmeric", "Cardamom", "Coriander", "Black Pepper", "Cumin",
    "Fenugreek", "Coconut", "Arecanut", "Tea", "Coffee", "Rubber",
    "Jute", "Tobacco", "Linseed", "Castor Seed", "Sesame", "Millets"
])

# --- API-based price fetcher with fallback ---
@st.cache_data(ttl=900)
def get_crop_price(state, crop):
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    base_params = {
        "api-key": "579b464db66ec23bdd00000109549b0bbfa64a427d252ce66872dfff",
        "format": "json",
        "filters[commodity]": crop,
        "limit": 50
    }
    try:
        # Try state-level first
        params = base_params.copy()
        params["filters[state]"] = state
        r = requests.get(url, params=params, timeout=10)
        records = r.json().get("records", [])
        if not records:
            # Fallback to all-India average
            params.pop("filters[state]", None)
            r = requests.get(url, params=params, timeout=10)
            records = r.json().get("records", [])
            if not records:
                return None, "No data"
            df = pd.DataFrame(records)
            df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
            return round(df["modal_price"].dropna().mean(), 2), "India"
        # State data
        df = pd.DataFrame(records)
        df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
        return round(df["modal_price"].dropna().mean(), 2), "State"
    except:
        return None, "Error"

# --- Page UI ---
def show_tracklist():
    lang = st.session_state.get("lang", "en")
    st.markdown(f"## 📋 {t('Track Your Crops', lang)}")

    # Load tracklist from file
    if "tracklist" not in st.session_state:
        st.session_state.tracklist = load_tracklist()

    crop = st.selectbox(t("Select Crop", lang), CROP_LIST)
    state = st.selectbox(
        t("Select State", lang),
        ["Maharashtra", "Punjab", "Uttar Pradesh", "Gujarat", "Karnataka",
         "Madhya Pradesh", "Haryana", "Rajasthan", "Tamil Nadu", "Telangana",
         "Bihar", "Odisha", "Assam", "Kerala", "West Bengal", "Chhattisgarh",
         "Andhra Pradesh", "Delhi", "Jharkhand", "Goa"]
    )

    if st.button(t("➕ Add to Tracklist", lang)):
        entry = {"crop": crop, "state": state}
        if entry not in st.session_state.tracklist:
            st.session_state.tracklist.append(entry)
            save_tracklist(st.session_state.tracklist)
            st.success(f"✅ {t('Added', lang)} {crop} ({state})")
        else:
            st.info(t("Already in your tracklist.", lang))

    # Show list
    if st.session_state.tracklist:
        st.markdown(f"### 🧾 {t('Your Tracked Crops', lang)}")
        for i, item in enumerate(st.session_state.tracklist):
            col1, col2, col3 = st.columns([3, 3, 1])
            with col1: st.write(f"🌾 **{item['crop']}**")
            with col2: st.write(f"📍 {item['state']}")
            with col3:
                if st.button(t('❌ Remove', lang), key=f"remove_{i}"):
                    st.session_state.tracklist.pop(i)
                    save_tracklist(st.session_state.tracklist)
                    st.success(f"{t('Removed', lang)} {item['crop']} ({item['state']})")
                    st.rerun()

        if st.button(t("🗑️ Clear All", lang)):
            st.session_state.tracklist = []
            save_tracklist([])
            st.rerun()
    else:
        st.info(t("ℹ️ No crops tracked yet. Add some above!", lang))

    # Live prices
    st.markdown("---")
    st.markdown(f"### 💹 {t('Live Market Prices', lang)}")
    if st.session_state.tracklist:
        for item in st.session_state.tracklist:
            price, level = get_crop_price(item["state"], item["crop"])
            if price:
                label = item["state"] if level == "State" else "All-India Avg"
                st.success(f"🌾 **{item['crop']} ({label})** — ₹{price}/Quintal")
            else:
                st.info(f"{t('No live data for', lang)} {item['crop']} {t('in', lang)} {item['state']}.")
