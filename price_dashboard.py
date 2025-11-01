import streamlit as st
import requests
import pandas as pd

# --- Load Global Theme ---
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

# --- CACHED DATA FETCHER ---
@st.cache_data(ttl=900)
def fetch_data(state, crop):
    """Fetch mandi price data from Agmarknet India API"""
    try:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "filters[state]": state,
            "filters[commodity]": crop,
            "limit": 50
        }
        res = requests.get(BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        if "records" in data and data["records"]:
            return pd.DataFrame(data["records"])
        else:
            return pd.DataFrame()  # empty DF if no records found

    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
        return pd.DataFrame()

# --- MAIN PAGE ---
def price_dashboard():
    st.title("🌾 Live Mandi Prices Dashboard")
    st.caption("Get real-time mandi prices of crops directly from Agmarknet India.")

    # --- Filters ---
    state = st.selectbox(
        "Select State",
        [
            "Maharashtra", "Punjab", "Uttar Pradesh",
            "Karnataka", "Gujarat", "Haryana", "Madhya Pradesh"
        ]
    )

    crop = st.text_input("Enter Crop Name", "Wheat")

    # --- Fetch and Display Data ---
    if st.button("🔍 Show Prices"):
        with st.spinner("Fetching data, please wait..."):
            df = fetch_data(state, crop)

        if not df.empty:
            df = df.rename(columns={
                "state": "State",
                "district": "District",
                "market": "Market",
                "commodity": "Crop",
                "min_price": "Min Price (₹/Quintal)",
                "max_price": "Max Price (₹/Quintal)",
                "modal_price": "Modal Price (₹/Quintal)",
                "arrival_date": "Date"
            })

            st.success(f"✅ Showing live mandi prices for **{crop}** in **{state}**")

            st.dataframe(
                df[
                    [
                        "State", "District", "Market", "Crop",
                        "Min Price (₹/Quintal)", "Max Price (₹/Quintal)",
                        "Modal Price (₹/Quintal)", "Date"
                    ]
                ],
                use_container_width=True
            )
        else:
            st.warning("⚠️ No data found for this crop and state. Try a different combination.")