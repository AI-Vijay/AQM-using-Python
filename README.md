# 🌿 ESP32 Real-Time Air Quality & Environmental Analytics

An IoT-based air quality monitoring and microclimate analytics system powered by an **ESP32 microcontroller**, **MQ-135 air quality sensor**, **DHT11/DHT22 temperature & humidity sensor**, and an interactive **Streamlit dashboard**.

The system fetches live sensor telemetry over HTTP, derives advanced physical and atmospheric parameters, logs historical readings locally, and provides intuitive visualizations for environmental analysis.

---

## 🚀 Key Features

- **Live Hardware Integration**: Connects to the ESP32 REST API (`/api/data`) to stream live Temperature, Relative Humidity, Raw Gas counts, and AQI.
- **Flexible Credential Configuration**: Easily manage Wi-Fi network credentials via `.env` or `secrets.h` header files without exposing credentials in source code.
- **Containerized Deployment**: Fully dockerized for seamless cross-platform execution with persistent volume mounts for historical data logs.
- **Resilient Offline Caching**: Automatically persists incoming readings locally and gracefully falls back to cached data if the hardware loses connectivity.
- **Derived Environmental Parameters**:
  - **Dew Point (°C)**: Calculates condensation temperature using the Magnus formula.
  - **Heat Index (°C)**: Computes apparent "feels-like" temperature using Rothfusz regression.
  - **Vapor Pressure Deficit (VPD in kPa)**: Evaluates air dryness and plant transpiration pressure.
  - **Absolute Humidity (g/m³)**: Calculates actual water vapor mass per volume of air.
  - **Sensor ADC Voltage (V) & Rs/R0 Ratio**: Converts raw 12-bit ADC values for hardware calibration.
  - **Estimated CO₂ / VOC (ppm)**: Approximates contaminant concentration curves from MQ-135 sensor resistance.
  - **Thermal Comfort & Risk Assessment**: Flags high mold risk, dry air, or heat stress conditions automatically.
- **Interactive Visualizations**: Custom Plotly gauge charts for AQI status and multi-axis historical trend lines using Streamlit.

---

## 🛠️ Hardware Requirements & Wiring

### Hardware Checklist
- **ESP32 Development Board** (NodeMCU-32S, ESP32-WROOM-32, or similar)
- **DHT11 or DHT22** Temperature & Humidity Sensor
- **MQ-135** Air Quality / Gas Sensor
- **10kΩ Resistor** (pull-up for DHT11/22 data line if module lacks built-in pullup)
- Breadboard & Jumper Wires

### Pin Wiring Schematic

| Component | Component Pin | ESP32 Pin | Notes |
| :--- | :--- | :--- | :--- |
| **DHT11 / DHT22** | VCC | 3.3V or 5V | Power supply |
| | GND | GND | Ground |
| | DATA / OUT | **GPIO 4** | Configured as `DHT_PIN` |
| **MQ-135** | VCC | 5V (VIN) | Standard 5V heating element |
| | GND | GND | Ground |
| | A0 (Analog Out) | **GPIO 34** | ADC1 input (`MQ135_PIN`) |

---

## 🔐 Wi-Fi & Environment Credentials Setup

Wi-Fi credentials can be configured using either `.env` or `secrets.h`.

### Option A: Using `secrets.h` (Recommended for Arduino IDE / PlatformIO)
1. Copy `secrets.h.example` to `secrets.h` in the project root directory:
   ```bash
   cp secrets.h.example secrets.h
   ```
2. Open `secrets.h` and edit your Wi-Fi SSID and password:
   ```cpp
   #ifndef SECRETS_H
   #define SECRETS_H

   #define WIFI_SSID "Your_WiFi_SSID"
   #define WIFI_PASSWORD "Your_WiFi_Password"

   #endif
   ```
3. Compile and upload `esp32_code.ino` to your ESP32. The sketch automatically detects and includes `secrets.h` if present.

### Option B: Using `.env` File
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with your Wi-Fi credentials and ESP32 IP address:
   ```env
   WIFI_SSID="Your_WiFi_SSID"
   WIFI_PASSWORD="Your_WiFi_Password"
   ESP32_IP="192.168.1.100"
   ```

---

## ⚡ Setup & Execution

### 1. ESP32 Firmware Flashing

1. Open `esp32_code.ino` in **Arduino IDE** or **VS Code with PlatformIO**.
2. Install required Arduino libraries via Library Manager:
   - **DHT sensor library** (by Adafruit)
   - **Adafruit Unified Sensor**
3. Create `secrets.h` (see [Credentials Setup](#-wi-fi--environment-credentials-setup)).
4. Select board **ESP32 Dev Module**, choose correct COM port, and click **Upload**.
5. Open Serial Monitor at **115200 baud** to view the connected IP address (e.g., `192.168.1.100`).

---

### 2. Streamlit Dashboard Setup

#### Local Python Environment

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r r.txt
   ```

4. **Configure ESP32 IP address:**
   Update `ESP32_IP` in `dashboard.py` (or set `.env` configuration) to match the IP shown in the ESP32 Serial Monitor.

5. **Run the Streamlit Dashboard:**
   ```bash
   streamlit run dashboard.py
   ```
6. Access the dashboard at `http://localhost:8501`.

---

## 🌐 REST API Endpoints

The ESP32 runs a REST API server on port 80.

### `GET /api/data`
Returns current sensor readings and calculated index in JSON format.

**Sample Response:**
```json
{
  "temperature": 24.5,
  "humidity": 55.0,
  "raw_gas": 3210,
  "aqi": 35,
  "air_quality": "Good",
  "aqi_type": "estimated_mq135_index"
}
```

### `GET /`
Returns basic service status text and endpoint guide.

---

## 📁 Repository Structure

```text
├── data/
│   ├── sensor_data.json       # Latest cached reading from ESP32
│   └── sensor_history.csv     # Historical sensor and derived telemetry logs
├── dashboard.py               # Streamlit real-time monitoring dashboard
├── esp32_code.ino             # ESP32 firmware C++ code
├── .env.example               # Environment variables template
├── secrets.h.example          # Wi-Fi credentials header template
├── r.txt                      # Python library dependencies
├── .gitignore                 # Excluded tracking for secrets and build artifacts
└── README.md                  # Project documentation
```

---

## 📝 License

Distributed under the MIT License.
