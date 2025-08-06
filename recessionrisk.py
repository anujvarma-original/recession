# recessionrisk.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from fredapi import Fred

st.set_page_config(page_title="Recession Risk Dashboard", layout="wide")

# Load API key from Streamlit secrets
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred(api_key=FRED_API_KEY)

# Define economic indicators and their FRED series IDs
INDICATORS = {
    "M2 Money Supply (YoY%)": "M2SL",
    "10Y-2Y Yield Spread (%)": ("GS10", "GS2"),
    "Unemployment Rate (%)": "UNRATE",
    "ISM Manufacturing PMI": "NAPMPI",
    "Housing Starts (Thousands)": "HOUST",
    "Consumer Confidence Index": "UMCSENT",
    "LEI (Leading Economic Index)": "USSLIND",
    "Credit Spread (BAA - AAA)": ("BAA", "AAA")
}

@st.cache_data(ttl=3600)
def safe_get_series(series_id):
    try:
        series = fred.get_series(series_id).dropna()
        if series.empty:
            raise ValueError("Empty series returned")
        return series
    except Exception as e:
        st.warning(f"Error retrieving {series_id}: {e}")
        return pd.Series(dtype='float64')

def compute_indicators():
    results = {}

    # M2 YoY%
    m2 = safe_get_series("M2SL")
    if not m2.empty:
        m2_today = m2.iloc[-1]
        m2_last_year = m2.asof(datetime.today() - timedelta(days=365))
        results["M2 Money Supply (YoY%)"] = ((m2_today - m2_last_year) / m2_last_year) * 100
    else:
        results["M2 Money Supply (YoY%)"] = None

    # Yield Curve (10Y - 2Y)
    gs10 = safe_get_series("GS10")
    gs2 = safe_get_series("GS2")
    if not gs10.empty and not gs2.empty:
        results["10Y-2Y Yield Spread (%)"] = gs10.iloc[-1] - gs2.iloc[-1]
    else:
        results["10Y-2Y Yield Spread (%)"] = None

    # Unemployment
    unrate = safe_get_series("UNRATE")
    results["Unemployment Rate (%)"] = unrate.iloc[-1] if not unrate.empty else None

    # ISM PMI
    pmi = safe_get_series("NAPMPI")
    results["ISM Manufacturing PMI"] = pmi.iloc[-1] if not pmi.empty else None

    # Housing Starts
    hous = safe_get_series("HOUST")
    results["Housing Starts (Thousands)"] = hous.iloc[-1] if not hous.empty else None

    # Consumer Confidence
    cci = safe_get_series("UMCSENT")
    results["Consumer Confidence Index"] = cci.iloc[-1] if not cci.empty else None

    # LEI
    lei = safe_get_series("USSLIND")
    results["LEI (Leading Economic Index)"] = lei.iloc[-1] if not lei.empty else None

    # Credit Spread
    baa = safe_get_series("BAA")
    aaa = safe_get_series("AAA")
    if not baa.empty and not aaa.empty:
        results["Credit Spread (BAA - AAA)"] = baa.iloc[-1] - aaa.iloc[-1]
    else:
        results["Credit Spread (BAA - AAA)"] = None

    return results

def assess_risk(indicators):
    score = 0
    total = 0

    # Assign weights or thresholds
    if indicators["M2 Money Supply (YoY%)"] is not None:
        total += 1
        if indicators["M2 Money Supply (YoY%)"] < 0:
            score += 1

    if indicators["10Y-2Y Yield Spread (%)"] is not None:
        total += 1
        if indicators["10Y-2Y Yield Spread (%)"] < 0:
            score += 1

    if indicators["Unemployment Rate (%)"] is not None:
        total += 1
        if indicators["Unemployment Rate (%)"] > 5:
            score += 1

    if indicators["ISM Manufacturing PMI"] is not None:
        total += 1
        if indicators["ISM Manufacturing PMI"] < 45:
            score += 1

    if indicators["Housing Starts (Thousands)"] is not None:
        total += 1
        if indicators["Housing Starts (Thousands)"] < 1000:
            score += 1

    if indicators["Consumer Confidence Index"] is not None:
        total += 1
        if indicators["Consumer Confidence Index"] < 60:
            score += 1

    if indicators["LEI (Leading Economic Index)"] is not None:
        total += 1
        if indicators["LEI (Leading Economic Index)"] < 0:
            score += 1

    if indicators["Credit Spread (BAA - AAA)"] is not None:
        total += 1
        if indicators["Credit Spread (BAA - AAA)"] > 2.0:
            score += 1

    if total == 0:
        return "UNKNOWN"

    ratio = score / total
    if ratio >= 0.6:
        return "HIGH"
    elif ratio >= 0.3:
        return "MEDIUM"
    else:
        return "LOW"

# ---------- UI ----------

st.title("📉 Recession Risk Dashboard")

with st.spinner("Fetching economic indicators..."):
    indicators = compute_indicators()
    risk = assess_risk(indicators)

st.header(f"🛑 Overall Recession Risk: {risk}")

st.subheader("📊 Indicator Summary")
df = pd.DataFrame(indicators.items(), columns=["Indicator", "Latest Value"])
st.dataframe(df.set_index("Indicator"), use_container_width=True)
