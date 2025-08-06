import streamlit as st
import pandas as pd
from fredapi import Fred
from datetime import datetime, timedelta

# Load API key from Streamlit secrets
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred(api_key=FRED_API_KEY)

st.set_page_config(page_title="Recession Risk Dashboard", layout="centered")
st.title("📉 Recession Risk Dashboard")
st.caption("Powered by FRED Economic Data")

# Define indicators and thresholds
indicators = {
    "M2SL": {"name": "M2 Money Supply YoY (%)", "threshold_low": 0, "threshold_high": -1},
    "Credit_Spread": {"name": "Credit Spread (BAA - AAA)", "threshold_low": 1.5, "threshold_high": 2.5},
    "Yield_Spread": {"name": "10Y - 2Y Yield Curve", "threshold_low": 0, "threshold_high": -0.5},
    "USSLIND": {"name": "Leading Economic Index", "threshold_low": 100, "threshold_high": 98},
    "UNRATE": {"name": "Unemployment Rate", "threshold_low": 4.5, "threshold_high": 5.5},
    "HOUST": {"name": "Housing Starts", "threshold_low": 1.5e6, "threshold_high": 1.3e6},
    "NAPM": {"name": "ISM Manufacturing PMI", "threshold_low": 50, "threshold_high": 47},
    "UMCSENT": {"name": "Consumer Confidence", "threshold_low": 80, "threshold_high": 70}
}

@st.cache_data
def get_latest_value(series_id):
    data = fred.get_series(series_id)
    return data.dropna().iloc[-1]

@st.cache_data
def compute_indicators():
    results = []
    scores = []

    for key, meta in indicators.items():
        if key == "Credit_Spread":
            baa = get_latest_value("BAA")
            aaa = get_latest_value("AAA")
            value = baa - aaa
        elif key == "Yield_Spread":
            gs10 = get_latest_value("GS10")
            gs2 = get_latest_value("GS2")
            value = gs10 - gs2
        elif key == "M2SL":
            today = datetime.today()
            last_year = today - timedelta(days=365)
            m2_today = fred.get_series("M2SL").dropna().iloc[-1]
            m2_last_year = fred.get_series("M2SL").asof(last_year)
            value = ((m2_today - m2_last_year) / m2_last_year) * 100
        else:
            value = get_latest_value(key)

        if value >= meta["threshold_low"]:
            risk = 0
        elif value >= meta["threshold_high"]:
            risk = 1
        else:
            risk = 2

        scores.append(risk)
        results.append({
            "Indicator": meta["name"],
            "Value": round(value, 2),
            "Risk Level": ["LOW", "MEDIUM", "HIGH"][risk]
        })

    avg_score = sum(scores) / len(scores)
    if avg_score >= 1.5:
        final_risk = "HIGH"
    elif avg_score >= 0.75:
        final_risk = "MEDIUM"
    else:
        final_risk = "LOW"

    return results, final_risk

# Compute and display
with st.spinner("Fetching latest economic data..."):
    results, overall_risk = compute_indicators()

st.subheader("📊 Indicator Status")
st.dataframe(pd.DataFrame(results))

st.markdown("---")
st.subheader("🧠 Overall Recession Risk")
st.markdown(f"### 🚨 **{overall_risk}**", unsafe_allow_html=True)
