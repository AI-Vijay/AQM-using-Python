
import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path

st.set_page_config(page_title="Mumbai AQI Predictor", page_icon="🌫️", layout="centered")

MODEL_PATH = Path(__file__).parent / "aqi_mumbai_model.joblib"
model = joblib.load(MODEL_PATH)

st.title("🌫️ Mumbai AQI Predictor")
st.write("Enter pollutant measurements and time information to estimate AQI.")

pollutants = ["PM2.5","PM10","NO","NO2","NOx","NH3","CO","SO2","O3","Benzene","Toluene","Xylene"]

values = {}
cols = st.columns(2)
for i, p in enumerate(pollutants):
    with cols[i % 2]:
        values[p] = st.number_input(p, min_value=0.0, value=0.0, step=0.1)

st.subheader("Time information")
c1, c2, c3, c4 = st.columns(4)
with c1:
    hour = st.number_input("Hour", 0, 23, 12)
with c2:
    day_of_week = st.number_input("Day of week", 0, 6, 0, help="Monday=0, Sunday=6")
with c3:
    month = st.number_input("Month", 1, 12, 1)
with c4:
    day_of_year = st.number_input("Day of year", 1, 366, 1)

if st.button("Predict AQI", type="primary"):
    row = values | {
        "hour": hour,
        "day_of_week": day_of_week,
        "month": month,
        "day_of_year": day_of_year
    }
    X = pd.DataFrame([row])
    aqi = float(model.predict(X)[0])
    aqi = max(0.0, aqi)

    if aqi <= 50:
        bucket = "Good"
    elif aqi <= 100:
        bucket = "Satisfactory"
    elif aqi <= 200:
        bucket = "Moderate"
    elif aqi <= 300:
        bucket = "Poor"
    elif aqi <= 400:
        bucket = "Very Poor"
    else:
        bucket = "Severe"

    st.metric("Predicted AQI", f"{aqi:.0f}")
    st.info(f"Estimated AQI category: **{bucket}**")
