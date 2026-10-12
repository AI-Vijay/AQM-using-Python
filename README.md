# 🌿 ESP32 Real-Time Air Quality & Environmental Analytics

An IoT-based air quality monitoring and microclimate analytics system powered by an **ESP32 microcontroller**, **MQ-135 air quality sensor**, and an interactive **Streamlit dashboard**. 

The system fetches live sensor telemetry over HTTP, derives advanced physical and atmospheric parameters, logs historical readings locally, and provides intuitive visualizations for environmental analysis.

---

## 🚀 Key Features

- **Live Hardware Integration**: Connects to the ESP32 REST API (`/api/data`) to stream live Temperature, Relative Humidity, Raw Gas counts, and AQI[cite: 1].
- **Containerized Deployment**: Fully dockerized for seamless cross-platform execution with persistent volume mounts for historical data logs.
- **Resilient Offline Caching**: Automatically persists incoming readings locally and gracefully falls back to cached data if the hardware loses connectivity[cite: 1].
- **Derived Environmental Parameters**:
  - **Dew Point (°C)**: Calculates condensation temperature using the Magnus formula.
  - **Heat Index (°C)**: Computes apparent "feels-like" temperature.
  - **Vapor Pressure Deficit (VPD in kPa)**: Evaluates air dryness and plant transpiration pressure.
  - **Absolute Humidity (g/m³)**: Calculates actual water vapor mass per volume of air.
  - **Sensor ADC Voltage (V) & Rs/R0 Ratio**: Converts raw 12-bit ADC values for hardware calibration.
  - **Estimated CO₂ / VOC (ppm)**: Approximates contaminant concentration curves from MQ-135 sensor resistance.
  - **Thermal Comfort & Risk Assessment**: Flags high mold risk, dry air, or heat stress conditions automatically.
- **Interactive Visualizations**: Custom Plotly gauge charts for AQI status and multi-axis historical trend lines using Streamlit tabs[cite: 5].

---

## 🛠️ Hardware Requirements

- **ESP32 Microcontroller** (configured with PlatformIO / Arduino framework)[cite: 1]
- **MQ-135 Gas Sensor** (connected to ESP32 ADC pin)[cite: 1]
- **DHT11 / DHT22 Sensor** (for temperature and humidity monitoring)[cite: 1]

---

## 📁 Repository Structure

```text
├── data/
│   ├── sensor_data.json       # Latest cached reading from ESP32
│   └── sensor_history.csv     # Historical sensor and derived telemetry logs
├── dashboard.py               # Streamlit real-time monitoring dashboard
├── r.txt                      # Python library dependencies
├── Dockerfile                 # Docker image configuration
├── docker-compose.yml         # Multi-container orchestration and volume mounts
├── .dockerignore              # Excluded files for optimized Docker builds
└── README.md                  # Project documentation

## ⚡ Setup & Execution

### Option 1: Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-folder>