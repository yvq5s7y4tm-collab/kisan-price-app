# state_districts.py
import json
import time
from pathlib import Path
from typing import List

import pandas as pd
import requests
import streamlit as st
import urllib.request
from translator import t


# Local storage
STATES_DISTRICTS_CSV = Path("states_districts.csv")
DISTRICT_MARKET_CACHE = Path("district_market_cache.json")

API_KEY = "579b464db66ec23bdd00000109549b0bbfa64a427d252ce66872dfff"
BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"


@st.cache_data(ttl=86400)
def build_states_districts_csv() -> pd.DataFrame:
    """Scrape Wikipedia for all Indian states and districts and cache locally."""
    if STATES_DISTRICTS_CSV.exists():
        df = pd.read_csv(STATES_DISTRICTS_CSV)
        df["state"] = df["state"].str.strip().str.title()
        df["district"] = df["district"].str.strip().str.title()
        return df

    url = "https://en.wikipedia.org/wiki/List_of_districts_in_India"

    # Send request with a browser-like user-agent to bypass 403 errors
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0 Safari/537.36"
            )
        },
    )

    with urllib.request.urlopen(req) as response:
        html = response.read().decode("utf-8")

    # Parse the main table
    tables = pd.read_html(html, match="State or UT")
    df = tables[0][["State or UT", "District"]].rename(
        columns={"State or UT": "state", "District": "district"}
    )

    df["state"] = df["state"].str.strip().str.title()
    df["district"] = df["district"].str.strip().str.title()

    # Cleanup
    df["state"] = df["state"].replace({
        "Nct Of Delhi": "Delhi",
        "Jammu And Kashmir": "Jammu and Kashmir",
        "Dadra And Nagar Haveli And Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
    })

    df = df.drop_duplicates().sort_values(["state", "district"]).reset_index(drop=True)
    df.to_csv(STATES_DISTRICTS_CSV, index=False)
    return df


@st.cache_data(ttl=86400)
def load_states() -> List[str]:
    """Return list of all states/UTs."""
    df = build_states_districts_csv()
    return sorted(df["state"].unique().tolist())


def _load_market_cache() -> dict:
    if DISTRICT_MARKET_CACHE.exists():
        try:
            return json.loads(DISTRICT_MARKET_CACHE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_market_cache(cache: dict):
    DISTRICT_MARKET_CACHE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _district_has_market(state: str, district: str, throttle: float = 0.35) -> bool:
    """Check if a district in a state has any market data available (cached)."""
    cache = _load_market_cache()
    key = f"{state}|{district}"
    if key in cache:
        return cache[key]

    params = {
        "api-key": API_KEY,
        "format": "json",
        "filters[state]": state,
        "filters[district]": district,
        "limit": 1,
    }

    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        has_market = False
        if r.status_code == 200:
            recs = r.json().get("records", [])
            has_market = len(recs) > 0
        cache[key] = has_market
        _save_market_cache(cache)
        time.sleep(throttle)
        return has_market
    except Exception:
        cache[key] = False
        _save_market_cache(cache)
        return False


@st.cache_data(show_spinner=False)
def get_districts_for_state(state: str, only_with_markets: bool = True) -> List[str]:
    """Return all districts for a state, optionally filtering those with markets."""
    df = build_states_districts_csv()
    districts = df[df["state"] == state]["district"].dropna().unique().tolist()
    districts = sorted(districts)

    if not only_with_markets:
        return districts

    valid = [d for d in districts if _district_has_market(state, d)]
    return valid
