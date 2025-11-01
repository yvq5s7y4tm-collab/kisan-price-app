import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
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

# --- API CONFIG ---
API_KEY = "579b464db66ec23bdd00000109549b0bbfa64a427d252ce66872dfff"
BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# --- CACHED FETCH FUNCTION ---
@st.cache_data(ttl=1800)
def fetch_price_history(state, crop):
    """Fetch crop price data for a given state from Agmarknet"""
    try:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "filters[state]": state,
            "filters[commodity]": crop,
            "limit": 500
        }
        r = requests.get(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get("records", [])
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
        df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
        df = df.dropna(subset=["arrival_date", "modal_price"])
        df = df.sort_values("arrival_date")

        return df

    except Exception as e:
        st.error(f"⚠️ Error fetching price history: {e}")
        return pd.DataFrame()

# --- MAIN PAGE FUNCTION ---
def price_tracking():
    """📉 Price Trend Analysis Page"""
    st.title("📉 Price Trend Analysis")
    st.caption("Visualize how mandi prices change over time for your chosen crop.")

    # --- Filters ---
    state = st.selectbox(
        "Select State",
        ["Maharashtra", "Punjab", "Uttar Pradesh", "Gujarat", "Karnataka"]
    )

    crop = st.selectbox(
        "Select Crop",
        ["Wheat", "Rice", "Cotton", "Maize", "Onion", "Tomato", "Bajra"]
    )

    # --- Button Action ---
    if st.button("📊 Show Trend"):
        with st.spinner("Fetching live mandi data..."):
            df = fetch_price_history(state, crop)

        if df.empty:
            st.warning("⚠️ No data found for this crop and state.")
            return

        # --- Compute Averages ---
        avg_df = df.groupby("arrival_date", as_index=False)["modal_price"].mean()

        # --- Metrics Section ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Highest Price", f"{avg_df['modal_price'].max():,.0f} ₹/Qtl")
        with col2:
            st.metric("Lowest Price", f"{avg_df['modal_price'].min():,.0f} ₹/Qtl")
        with col3:
            st.metric("Average Price", f"{avg_df['modal_price'].mean():,.0f} ₹/Qtl")

        # --- Price Trend Chart ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=avg_df["arrival_date"],
            y=avg_df["modal_price"],
            mode="lines+markers",
            name=crop,
            line=dict(color="#0b3b2e", width=3),
            marker=dict(size=6, color="#1b5e20"),
            hovertemplate="%{x|%d %b %Y}<br>Price: %{y:,.0f} ₹/Qtl"
        ))

        fig.update_layout(
            title=f"📈 {crop} Price Trend in {state}",
            xaxis_title="Date",
            yaxis_title="Price (₹/Quintal)",
            template="plotly_white",
            plot_bgcolor="#f8fff9",
            paper_bgcolor="#ffffff",
            hovermode="x unified",
            font=dict(size=14, family="Lato, sans-serif", color="#0b3b2e"),
            margin=dict(l=30, r=30, t=60, b=30)
        )

        st.plotly_chart(fig, use_container_width=True)
