import streamlit as st
import pydeck as pdk
import pandas as pd
import requests
import json
from pathlib import Path
from translator import t
import streamlit as st
import pandas as pd
import requests
from translator import t   # if you need language later

def load_theme():
    try:
        with open("theme.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

load_theme()


# --- Load Theme ---
def load_theme():
    try:
        with open("theme.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

load_theme()

# --- File Paths ---
RAW_FILE = Path("mandis_raw.csv")
GEO_FILE = Path("mandis_geocoded.csv")
GEOCACHE_FILE = Path("geocache.json")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

@st.cache_data(ttl=600)
def get_user_location():
    """Detect user’s location using IP."""
    try:
        res = requests.get("https://ipapi.co/json/", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {
                "city": data.get("city"),
                "region": data.get("region"),
                "country": data.get("country_name"),
                "lat": data.get("latitude"),
                "lon": data.get("longitude")
            }
    except:
        pass
    return None

@st.cache_data(ttl=3600)
def load_geo():
    """Load pre-geocoded mandis data."""
    if GEO_FILE.exists():
        return pd.read_csv(GEO_FILE)
    return pd.DataFrame(columns=["name", "state", "district", "latitude", "longitude"])

def show_market_locator():
    """Main Market Locator Page."""
    lang = st.session_state.get("lang", "en")
 
    st.title("📍 " + t("Market Locator", lang))
    st.caption(t("Find nearby mandis and open them in Google Maps.", lang))

    # Detect user location
    loc = get_user_location()
    if loc:
        st.success(f"📍 {t('Detected', lang)}: {loc['city']}, {loc['region']} ({loc['country']})")
        user_lat, user_lon = loc["lat"], loc["lon"]
    else:
        st.warning(t("Could not detect location automatically.", lang))
        user_lat, user_lon = 21.0, 78.0  # Center of India

    df = load_geo()
    if df.empty:
        st.warning(t("⚠️ No mandi data found. Please add mandis to file.", lang))
        return

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Filters
    states = sorted(df["state"].dropna().unique())
    state = st.selectbox(t("Select State", lang), states)
    search = st.text_input(t("Search by Market or District", lang), "")

    filtered = df[df["state"] == state]
    if search.strip():
        search_lower = search.strip().lower()
        filtered = filtered[
            filtered["name"].str.lower().str.contains(search_lower, na=False) |
            filtered["district"].str.lower().str.contains(search_lower, na=False)
        ]

    st.subheader(f"🧭 {t('Mandis List', lang)}")
    st.dataframe(filtered[["name", "district", "state"]].reset_index(drop=True), use_container_width=True)

    # Map
    map_df = filtered.dropna(subset=["latitude", "longitude"]).rename(columns={"latitude": "lat", "longitude": "lon"})
    if not map_df.empty:
        center_lat = user_lat if loc else map_df["lat"].mean()
        center_lon = user_lon if loc else map_df["lon"].mean()

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[lon, lat]',
            get_fill_color='[30, 180, 50, 200]',
            get_radius=80000,
            pickable=True,
        )
        view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=5)
        tooltip = {
            "html": "<b>{name}</b><br>{district}, {state}<br><a href='https://www.google.com/maps?q={lat},{lon}' target='_blank'>📍 Open in Maps</a>",
            "style": {"backgroundColor": "white", "color": "black"}
        }

        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))
    else:
        st.info(t("No coordinates found for this filter.", lang))
