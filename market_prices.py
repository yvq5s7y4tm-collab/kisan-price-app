import streamlit as st
import requests
import pandas as pd

# --- Load Theme ---
def load_theme():
    """Load global theme styles from theme.css"""
    try:
        with open("theme.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"⚠️ Could not load theme: {e}")

load_theme()

# --- API CONFIG ---
API_KEY = "579b464db66ec23bdd00000109549b0bbfa64a427d252ce66872dfff"
BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# --- CACHED PRICE FETCHER ---
@st.cache_data(ttl=3600)
def get_market_price(state, crop):
    """Fetch the latest mandi price for a specific crop and state."""
    params = {
        "api-key": API_KEY,
        "format": "json",
        "filters[state]": state,
        "filters[commodity]": crop,
        "limit": 10
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        records = res.json().get("records", [])
        if not records:
            return None

        df = pd.DataFrame(records)
        df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
        df = df.dropna(subset=["modal_price"])
        latest = df.iloc[-1]

        return {
            "market": latest.get("market", "Unknown"),
            "price": latest["modal_price"],
            "date": latest.get("arrival_date", "")
        }

    except Exception as e:
        st.error(f"❌ Error fetching price for {crop}: {e}")
        return None


# --- DISPLAY SECTION ---
def show_market_prices(state):
    """Display three main crop prices as styled cards."""
    st.subheader("💰 Real-Time Market Prices")

    crops = ["Cotton", "Wheat", "Jowar"]
    cols = st.columns(3)

    for i, crop in enumerate(crops):
        with cols[i]:
            st.markdown(f"### 🌾 {crop}")

            price_data = get_market_price(state, crop)
            if price_data:
                price_value = f"{price_data['price']:,.0f} ₹/Quintal"
                date = price_data['date'] or "—"

                st.markdown(f"""
                <div class="price-card">
                    <div class="price-title">{price_data['market']}</div>
                    <div class="price-val">{price_value}</div>
                    <div class="price-date">📅 Updated: {date}</div>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.info("No data found for this crop.")