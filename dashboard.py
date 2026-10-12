import streamlit as st
import requests
import json
import csv
import math
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# =====================================================
# CONFIGURATION
# =====================================================

ESP32_IP = "192.168.43.147"
API_URL = f"http://{ESP32_IP}/api/data"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

LATEST_JSON_FILE = DATA_DIR / "sensor_data.json"
HISTORY_CSV_FILE = DATA_DIR / "sensor_history.csv"

# =====================================================
# STREAMLIT PAGE CONFIG & STYLES
# =====================================================

st.set_page_config(
    page_title="Air Quality & Environmental Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .guide-card {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid #2196F3;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================
# SAFE DERIVED PARAMETER COMPUTATIONS
# =====================================================

def calculate_derived_parameters(temp_c, rh, raw_gas):
    """Derives environmental parameters safely from core sensor readings."""
    
    # Clamp input values to prevent mathematical domain errors
    safe_rh = max(0.1, min(100.0, float(rh)))
    safe_temp = float(temp_c)
    safe_raw_gas = max(0, int(raw_gas))

    # 1. Dew Point (°C) - Magnus Formula
    a, b = 17.625, 243.04
    try:
        gamma = (a * safe_temp) / (b + safe_temp) + math.log(safe_rh / 100.0)
        dew_point = (b * gamma) / (a - gamma)
    except (ValueError, ZeroDivisionError):
        dew_point = safe_temp

    # 2. Heat Index (°C) - Rothfusz regression approximation
    tf = (safe_temp * 9/5) + 32
    hi_f = 0.5 * (tf + 61.0 + ((tf - 68.0) * 1.2) + (safe_rh * 0.094))
    if hi_f >= 80:
        hi_f = (-42.379 + 2.04901523*tf + 10.14333127*safe_rh 
                - 0.22475541*tf*safe_rh - 0.00683783*tf*tf 
                - 0.05481717*safe_rh*safe_rh + 0.00122874*tf*tf*safe_rh 
                + 0.00085282*tf*safe_rh*safe_rh - 0.00000199*tf*tf*safe_rh*safe_rh)
    heat_index = (hi_f - 32) * 5/9

    # 3. Vapor Pressure Deficit (VPD in kPa)
    vp_sat = 0.61078 * math.exp((17.27 * safe_temp) / (safe_temp + 237.3))
    vp_act = vp_sat * (safe_rh / 100.0)
    vpd = max(0.0, vp_sat - vp_act)

    # 4. Absolute Humidity (g/m³)
    abs_humidity = (6.112 * math.exp((17.67 * safe_temp) / (safe_temp + 243.5)) * safe_rh * 2.1674) / (273.15 + safe_temp)

    # 5. ADC Voltage & Gas Sensor Resistance Ratio (Rs/R0)
    voltage = (safe_raw_gas / 4095.0) * 3.3
    voltage_clamped = max(0.01, min(3.29, voltage))
    rs_r0 = (3.3 - voltage_clamped) / voltage_clamped

    # 6. Estimated CO2 equivalent (ppm approximation)
    est_co2_ppm = max(400, int(116.602 * math.pow(max(0.1, rs_r0), -2.769)))

    # 7. Thermal Comfort Status
    comfort_status = "Ideal"
    if safe_rh > 70 and safe_temp > 20:
        comfort_status = "Mold Risk High"
    elif safe_temp > 32:
        comfort_status = "Heat Stress Risk"
    elif safe_rh < 30:
        comfort_status = "Air Too Dry"

    return {
        "dew_point": round(dew_point, 2),
        "heat_index": round(heat_index, 2),
        "vpd": round(vpd, 3),
        "abs_humidity": round(abs_humidity, 2),
        "voltage": round(voltage, 2),
        "rs_r0": round(rs_r0, 2),
        "est_co2_ppm": est_co2_ppm,
        "comfort_status": comfort_status
    }


# =====================================================
# DATA PERSISTENCE
# =====================================================

def save_json(data):
    cached_data = data.copy()
    cached_data["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LATEST_JSON_FILE, "w") as file:
        json.dump(cached_data, file, indent=4)

def load_saved_json():
    if not LATEST_JSON_FILE.exists():
        return None
    try:
        with open(LATEST_JSON_FILE, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return None

def save_history(data, derived):
    file_exists = HISTORY_CSV_FILE.exists()
    with open(HISTORY_CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                "timestamp", "temperature", "humidity", "raw_gas", "aqi", "air_quality",
                "dew_point", "heat_index", "vpd", "abs_humidity", "voltage", "est_co2_ppm"
            ])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data["temperature"], data["humidity"], data["raw_gas"], data["aqi"], data["air_quality"],
            derived["dew_point"], derived["heat_index"], derived["vpd"], derived["abs_humidity"],
            derived["voltage"], derived["est_co2_ppm"]
        ])


# =====================================================
# UI VISUALS
# =====================================================

def create_aqi_gauge(aqi_value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=aqi_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "AQI Index", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [None, 300], 'tickwidth': 1},
            'bar': {'color': "#2b2b2b"},
            'steps': [
                {'range': [0, 50], 'color': '#00E400'},
                {'range': [51, 100], 'color': '#FFFF00'},
                {'range': [101, 150], 'color': '#FF7E00'},
                {'range': [151, 200], 'color': '#FF0000'},
                {'range': [201, 300], 'color': '#8F3F97'}
            ]
        }
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=20))
    return fig


# =====================================================
# BEGINNER PARAMETER GUIDE COMPONENT
# =====================================================

def render_parameter_guide():
    st.divider()
    st.subheader("📚 Beginner's Guide to Understanding Dashboard Parameters")
    st.write("New to environmental monitoring? Here is a simple explanation of what each parameter measures and why it matters.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 🌡️ Thermal & Moisture Parameters

        * **Temperature (°C)**  
          *What it is:* Standard measurement of how warm or cold the air is.  
          *Ideal Range:* **20°C – 26°C** for indoor room comfort.

        * **Relative Humidity (%)**  
          *What it is:* The percentage of water vapor currently in the air compared to the maximum amount the air can hold at that temperature.  
          *Ideal Range:* **30% – 60%**. High humidity promotes mold growth, while low humidity causes dry skin and throat irritation.

        * **Heat Index (°C)**  
          *What it is:* The "feels-like" temperature. High humidity prevents sweat from evaporating, making warm air feel even hotter to the human body.

        * **Dew Point (°C)**  
          *What it is:* The exact temperature air needs to cool down to for water droplet condensation (dew/fog) to form. If Dew Point is close to Temperature, the air feels muggy and sticky.

        * **Absolute Humidity ($g/m^3$)**  
          *What it is:* The exact weight of water vapor contained in one cubic meter of air, regardless of temperature.
        """)

    with col2:
        st.markdown("""
        #### 💨 Air Quality & Sensor Engineering Metrics

        * **AQI (Air Quality Index)**  
          *What it is:* A standard 0–500 scale that tells you how clean or polluted the surrounding air is.  
          *Good Range:* **0 – 50** (Safe) | **>100** (Unhealthy for sensitive groups).

        * **Vapor Pressure Deficit (VPD in kPa)**  
          *What it is:* Measures how "dry" the air feels to plants and lungs. It is the gap between maximum saturation pressure and current moisture pressure.  
          *Ideal Range:* **0.8 – 1.2 kPa**. Very useful in greenhouses and plant growth rooms.

        * **Est. $CO_2$ / VOC (ppm)**  
          *What it is:* An estimated count of Parts-Per-Million ($ppm$) of carbon dioxide and Volatile Organic Compounds derived from the MQ-135 gas sensor.  
          *Ideal Range:* **400 – 1000 ppm**. Above 1000 ppm usually indicates bad ventilation.

        * **ADC Voltage ($V$) & Raw Counts**  
          *What it is:* The direct electrical reading on the ESP32 chip pin (0 to 4095 raw value mapped to 0.0V – 3.3V). Higher values mean higher gas/smoke concentrations detected.
        """)


# =====================================================
# DISPLAY DASHBOARD
# =====================================================

def display_dashboard(data, connected):
    temp = float(data["temperature"])
    rh = float(data["humidity"])
    raw_gas = int(data["raw_gas"])
    aqi = int(data["aqi"])
    air_quality = data["air_quality"]

    derived = calculate_derived_parameters(temp, rh, raw_gas)

    if connected:
        save_history(data, derived)

    # Status Header
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("🌿 ESP32 Air Quality & Environmental Analytics")
    with c2:
        if connected:
            st.success(f"🟢 Connected\n\n_{data.get('saved_at', 'Now')}_")
        else:
            st.warning(f"🟡 Offline\n\n_{data.get('saved_at', 'Cached')}_")

    st.divider()

    # Section 1: Main Environmental Overview
    st.subheader("📊 Core Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🌡️ Temperature", f"{temp:.1f} °C", delta=f"{derived['heat_index'] - temp:+.1f} °C HeatIdx")
    m2.metric("💧 Humidity", f"{rh:.1f} %", delta=f"{derived['dew_point']:.1f} °C Dew Pt")
    m3.metric("📊 Air Quality Index", aqi)
    m4.metric("⚡ ADC Voltage", f"{derived['voltage']} V")
    m5.metric("💨 Est. CO₂ / VOC", f"{derived['est_co2_ppm']} ppm")

    st.divider()

    # Section 2: AQI Visual Gauge & Thermal Comfort Details
    col_left, col_right = st.columns([1, 1.5])

    with col_left:
        st.subheader("AQI Status")
        st.plotly_chart(create_aqi_gauge(aqi), use_container_width=True)
        st.info(f"**Classification:** {air_quality} | **Comfort Status:** {derived['comfort_status']}")

    with col_right:
        st.subheader("🔬 Atmospheric Calculations")
        d1, d2 = st.columns(2)
        d1.metric("Vapor Pressure Deficit (VPD)", f"{derived['vpd']} kPa")
        d1.metric("Absolute Humidity", f"{derived['abs_humidity']} g/m³")
        d2.metric("Gas Sensor Ratio (Rs/R0)", f"{derived['rs_r0']}")
        d2.metric("Raw MQ-135 Counts", raw_gas)

    # Section 3: Historical Trend Visualizations
    st.divider()
    st.subheader("📈 Historical Trends")

    if HISTORY_CSV_FILE.exists():
        df = pd.read_csv(HISTORY_CSV_FILE)
        
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Compute missing derived columns safely for legacy CSV records
            if "heat_index" not in df.columns or "dew_point" not in df.columns:
                for idx, row in df.iterrows():
                    calc = calculate_derived_parameters(
                        float(row["temperature"]), 
                        float(row["humidity"]), 
                        int(row["raw_gas"])
                    )
                    df.at[idx, "heat_index"] = calc["heat_index"]
                    df.at[idx, "dew_point"] = calc["dew_point"]
                    df.at[idx, "vpd"] = calc["vpd"]
                    df.at[idx, "est_co2_ppm"] = calc["est_co2_ppm"]

            recent_df = df.tail(100)
            tab1, tab2, tab3 = st.tabs(["Temperature & Humidity", "Air Quality & Gas", "VPD & Dew Point"])

            with tab1:
                df_temp = recent_df.melt(
                    id_vars=["timestamp"], 
                    value_vars=["temperature", "heat_index", "dew_point"],
                    var_name="Metric", 
                    value_name="Value"
                )
                fig_temp = px.line(df_temp, x="timestamp", y="Value", color="Metric", title="Temperature & Thermal Indices (°C)")
                st.plotly_chart(fig_temp, use_container_width=True)

            with tab2:
                df_aqi = recent_df.melt(
                    id_vars=["timestamp"], 
                    value_vars=["aqi", "est_co2_ppm"],
                    var_name="Metric", 
                    value_name="Value"
                )
                fig_aqi = px.line(df_aqi, x="timestamp", y="Value", color="Metric", title="AQI and Estimated CO₂ Levels")
                st.plotly_chart(fig_aqi, use_container_width=True)

            with tab3:
                fig_vpd = px.line(recent_df, x="timestamp", y="vpd", labels={"vpd": "kPa"}, title="Vapor Pressure Deficit (VPD in kPa)")
                st.plotly_chart(fig_vpd, use_container_width=True)

    # Section 4: Beginner Educational Guide
    render_parameter_guide()


# =====================================================
# REAL-TIME EXECUTION LOOP
# =====================================================

@st.fragment(run_every="2s")
def realtime_dashboard():
    data = None
    connected = False

    try:
        response = requests.get(API_URL, timeout=3)
        if response.status_code == 200:
            fresh_data = response.json()
            save_json(fresh_data)
            data = load_saved_json()
            connected = True
        else:
            data = load_saved_json()
    except requests.exceptions.RequestException:
        data = load_saved_json()

    if data is not None:
        display_dashboard(data=data, connected=connected)
    else:
        st.error("🔴 ESP32 is not connected and no cached data is available.")

realtime_dashboard()