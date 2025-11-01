import requests
import streamlit as st
from translator import t


# --- Load Global Theme ---
def load_theme():
    """Load global theme styles from theme.css"""
    try:
        with open("theme.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"⚠️ Could not load theme: {e}")

load_theme()

# --- Detect Location ---
def get_user_city():
    """Detect approximate city using IP address."""
    try:
        res = requests.get("https://ipinfo.io", timeout=5)
        data = res.json()
        return data.get("city", "Delhi")  # fallback
    except Exception:
        return "Delhi"

# --- Weather Fetch ---
@st.cache_data(ttl=600)
def get_weather(api_key: str, city: str):
    """Fetch weather data from OpenWeather API."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    try:
        res = requests.get(url, params=params, timeout=8)
        res.raise_for_status()
        data = res.json()
        return {
            "city": data["name"],
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "description": data["weather"][0]["description"].capitalize(),
            "icon": data["weather"][0]["icon"]
        }
    except Exception as e:
        st.error(f"❌ Error fetching weather data: {e}")
        return None

# --- Display Weather Card ---
def show_weather():
    """Auto-detect location and display weather card."""
    api_key = "0c83443092f8d6fb4a9cc325006d26da"
    city = get_user_city()
    weather = get_weather(api_key, city)

    st.markdown('<div class="weather-card">', unsafe_allow_html=True)
    if weather:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(f"http://openweathermap.org/img/wn/{weather['icon']}@2x.png", width=60)
        with col2:
            st.markdown(f"### 🌤️ {weather['city']}")
            st.markdown(f"<b>{weather['temp']}°C</b> — {weather['description']}", unsafe_allow_html=True)
            st.caption(f"Feels like {weather['feels_like']}°C")
    else:
        st.info("🌦️ Weather data unavailable.")
    st.markdown("</div>", unsafe_allow_html=True)
