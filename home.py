import streamlit as st
import pandas as pd
import requests
from price_dashboard import fetch_data
from translator import t
import json
from pathlib import Path

# --- Tracklist persistence ---
TRACKLIST_FILE = Path("tracklist_data.json")

def load_tracklist():
    if TRACKLIST_FILE.exists():
        with open(TRACKLIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# --- Load Theme ---
def load_theme():
    try:
        with open("theme.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

load_theme()

# --- Weather Fetch ---
@st.cache_data(ttl=600)
def get_weather_by_city(city):
    key = "0c83443092f8d6fb4a9cc325006d26da"
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": key, "units": "metric"},
            timeout=8
        )
        data = r.json()
        return {"temp": data["main"]["temp"], "desc": data["weather"][0]["main"]}
    except:
        return {"temp": None, "desc": "Unavailable"}

# --- Optimized Crop Prices Fetch (with fallback) ---
@st.cache_data(ttl=900)
def get_all_crop_prices(state, crops):
    """Fetch mandi prices for user’s tracked crops (with all-India fallback)."""
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    results = []

    for crop in crops:
        params = {
            "api-key": "579b464db66ec23bdd00000109549b0bbfa64a427d252ce66872dfff",
            "format": "json",
            "filters[state]": state,
            "filters[commodity]": crop,
            "limit": 30
        }
        try:
            r = requests.get(url, params=params, timeout=8)
            records = r.json().get("records", [])
            if not records:
                # Fallback to all-India average if state-level unavailable
                params.pop("filters[state]", None)
                r = requests.get(url, params=params, timeout=8)
                records = r.json().get("records", [])

            if records:
                df = pd.DataFrame(records)
                df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
                avg = df["modal_price"].dropna().mean()
                if not pd.isna(avg):
                    results.append({
                        "crop": crop,
                        "price": round(avg, 2),
                        "market": df["market"].iloc[-1]
                    })
        except:
            continue

    return sorted(results, key=lambda x: x["price"], reverse=True)

# --- Units Map ---
UNIT_MAP = {
    "Cotton": "Ton", "Sugarcane": "Ton", "Banana": "Kg", "Apple": "Kg", "Mango": "Kg",
    "Orange": "Kg", "Tomato": "Kg", "Potato": "Kg", "Onion": "Kg", "Pomegranate": "Kg",
    "Papaya": "Kg", "Chilli": "Kg", "Grapes": "Kg", "Wheat": "Quintal", "Rice": "Quintal",
    "Maize": "Quintal", "Barley": "Quintal", "Bajra": "Quintal", "Jowar": "Quintal",
    "Ragi": "Quintal", "Mustard": "Quintal", "Groundnut": "Quintal", "Soyabean": "Quintal",
    "Sunflower": "Quintal", "Tur": "Quintal", "Urad": "Quintal", "Moong": "Quintal",
    "Gram": "Quintal", "Masoor": "Quintal"
}

# --- MAIN HOME FUNCTION ---
def home():
    lang_code = st.session_state.get("lang", "en")

    # Load saved crops into session
    if "tracklist" not in st.session_state:
        st.session_state.tracklist = load_tracklist()

    # 🌦️ Weather Section
    st.markdown(f"## 🌦️ {t('Weather Update', lang_code)}")
    city = st.selectbox(t("City / शहर", lang_code),
                        ["Jalgaon", "Amritsar", "Lucknow", "Surat", "Delhi", "Mumbai"])
    weather = get_weather_by_city(city)
    temp = f"{weather['temp']}°C" if weather["temp"] else "--"
    st.markdown(f"### {city} — {temp} ({weather['desc']})")

    st.markdown("---")

    # 💰 Market Prices
    st.markdown(f"## 💰 {t('State-wise Market Prices', lang_code)}")
    state = st.selectbox(t("Select State", lang_code),
                         ["Maharashtra", "Punjab", "Uttar Pradesh", "Gujarat", "Karnataka",
                          "Madhya Pradesh", "Haryana", "Rajasthan", "Tamil Nadu", "Telangana",
                          "Bihar", "Odisha", "Assam", "Kerala", "West Bengal", "Chhattisgarh",
                          "Andhra Pradesh", "Delhi", "Jharkhand", "Goa"])

    # 🌾 Crop Tracklist
    st.markdown(f"## 🌾 {t('Crop Tracklist', lang_code)}")

    if "tracklist" in st.session_state and st.session_state.tracklist:
        crops = [item["crop"] for item in st.session_state.tracklist]
        with st.spinner("Fetching live mandi data..."):
            data = get_all_crop_prices(state, crops)
        if not data:
            st.warning("⚠️ No live data found for your tracked crops in this state.")
            return
    else:
        st.info("⚠️ No crops added yet. Go to Tracklist page to add your crops.")
        return

    # Display Cards
    for d in data:
        unit = UNIT_MAP.get(d["crop"], "Quintal")
        st.markdown(f"""
        <div class="price-card">
            <div class="price-title">🌾 {d['crop']}</div>
            <div style="font-size:13px;color:#666;">{d['market']}, {state}</div>
            <div class="price-val">₹ {d['price']:,} / {unit}</div>
        </div>
        """, unsafe_allow_html=True)

    st.caption("📈 Market prices sourced live from Agmarknet (data.gov.in).")
