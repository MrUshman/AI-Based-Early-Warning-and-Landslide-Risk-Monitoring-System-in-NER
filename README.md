# AI-Based Early Warning and Landslide Risk Monitoring System in NER, India

An enterprise-grade, academic geotechnical monitoring and disaster early-warning web platform designed for India's **North-East Region (NER)** — spanning Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, and Tripura.

Powered by a trained **Random Forest Machine Learning Classifier**, **Leaflet Geospatial GIS**, and **Open-Meteo Real-Time Weather Integration**, this platform predicts slope failure probabilities hours before catastrophic collapse, enabling District Disaster Management Authorities (DDMA) and highway patrols to act proactively.

---

## 🌟 Key Features

1. **Interactive Geospatial GIS Surveillance Map (Leaflet.js)**
   - Live spatial map centered on North-East India showing all 12 strategic monitoring corridors (e.g., NH-10 Sikkim, NH-6 Meghalaya, Hunthar Veng Mizoram, NH-29 Nagaland).
   - Color-coded risk pins: 🟢 Low, 🟡 Moderate, 🟠 High, 🔴 Critical, with interactive popups displaying live slope angle, soil type, elevation, and instant weather status.

2. **Genuine Machine Learning Risk Engine (`RandomForestClassifier`)**
   - Trained on 3,000 geotechnical samples modeled after Geological Survey of India (GSI) susceptibility criteria and IMD rainfall intensity-duration thresholds.
   - Evaluates 7 core features: 24h Rainfall, 72h Cumulative Rainfall, Soil Moisture %, Slope Angle, Ground Vibration/Seismic Index, Station Elevation, and Soil Type (Clay, Silt, Loam, Rocky, Sandy).
   - Outputs continuous risk score (0–100), hazard level, class probability distribution, and explainable factor breakdowns.

3. **Live Weather API Integration (Open-Meteo)**
   - Click **"Sync Live Weather"** on any station page to fetch live real-time precipitation, temperature, and relative humidity for the exact latitude/longitude of that site.

4. **IoT Telemetry REST API & Streaming Simulator**
   - `POST /api/readings/`: Ingests JSON packets from field rain gauges, TDR soil moisture sensors, and tiltmeters.
   - Includes `simulate_iot_stream.py` to stream live sensor packets from your terminal during your college project presentation!

5. **Early Warning Hazards & Officer Acknowledgment**
   - Automatically generates emergency hazard bulletins whenever predicted risk reaches **High** or **Critical**.
   - Includes an officer response workflow with timestamped acknowledgments and standard operating procedures (SOP).

6. **Interactive Risk Simulator (With Viva Presets)**
   - Test extreme environmental scenarios with 1 click:
     - 🚨 *Monsoon Cloudburst (Critical)*
     - ⚠️ *Continuous Heavy Rain (High)*
     - 🌦️ *Moderate Pre-Monsoon*
     - ✅ *Stable Dry Weather (Low)*

7. **Official Disaster Management Reports & CSV Export**
   - 1-click export of alerts and raw sensor telemetry logs to CSV for civil defense records.

---

## 🛠️ System Architecture

```
[ Field IoT Sensors / Microcontrollers ] 
           │
           ▼
[ Django REST API: /api/readings/ ] <─── [ Open-Meteo Live Weather API ]
           │
           ▼
[ ML Risk Engine: RandomForestClassifier (120 Trees) ]
   ├── 24h Rainfall (mm)
   ├── 72h Rainfall (mm)
   ├── Volumetric Soil Moisture (%)
   ├── Slope Angle (degrees)
   ├── Ground Vibration / Seismic Index (0-10)
   ├── Station Elevation (m)
   └── Soil Type (Clay, Silt, Loam, Rocky, Sandy)
           │
           ▼
[ Risk Evaluation: Score (0-100) + Hazard Tier (Low/Mod/High/Crit) ]
           │
    ┌──────┴──────────────────────────┐
    ▼                                 ▼
[ Interactive Leaflet GIS Map ]   [ Emergency Alert Dispatch ]
```

---

## 🚀 Quick Start Guide (How to Run)

### 1. Open the project in VS Code / Terminal
```bash
cd c:\landslide-ews-ner
```

### 2. Activate Virtual Environment & Install Dependencies
```bash
# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. (Optional) Re-train the Machine Learning Model
```bash
python monitoring/ml/train.py
```
*Outputs: `landslide_rf_model.joblib`, `model_metrics.json`, and `synthetic_ner_landslide_dataset.csv`.*

### 4. Migrate Database & Seed NER Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 5. Launch the Server
```bash
python manage.py runserver
```
Open **http://127.0.0.1:8000/** in your browser.

---

## 🔑 Demo Evaluator Credentials

| Username | Password  | Role |
| :--- | :--- | :--- |
| `admin` | `admin123` | Senior Disaster Management Officer & Superuser |

---

## 🎬 How to Present This in College (Demo Flow)

1. **Dashboard Overview**:
   - Open the homepage to show the KPI stat cards (Monitored Stations, Telemetry, Active Warnings, Critical Hazards).
   - Point out the **Interactive Leaflet GIS Map** displaying stations across Sikkim, Meghalaya, Mizoram, Nagaland, and Assam. Click on a marker to show the pop-up details.
2. **AI Model & Metrics Page**:
   - Navigate to **AI Model** in the navbar.
   - Show the **Confusion Matrix**, **Feature Importances Bar Chart** (highlighting that Rainfall and Slope Angle are the top predictors), and **Per-Class Precision & Recall**.
3. **Live Weather Sync**:
   - Click on **Stations** → Select **Sonapur Tunnel Area, NH-6 (Meghalaya)**.
   - Click **"Sync Live Weather (Open-Meteo)"** to show real-time weather being pulled via API and evaluated on the spot!
4. **Live IoT Terminal Demonstration**:
   - Open a second terminal window and run:
     ```bash
     python simulate_iot_stream.py --count 5 --interval 2
     ```
   - Watch real-time sensor packets stream to the API and evaluate live in the terminal!
5. **Risk Simulator**:
   - Go to **Risk Simulator** and click the **"Monsoon Cloudburst"** preset to show instant risk scoring and emergency SOP recommendations.

---

## 🧪 Unit Testing

Run the full automated test suite (verifying ML predictions, REST APIs, CSV exports, and views):
```bash
python manage.py test
```

---

## 🎓 Viva / Examiner Q&A Guide

**Q1: Why did you choose Random Forest instead of a simple linear formula or neural network?**
> *Answer:* Landslide occurrences are governed by non-linear physical thresholds. For example, a 42° slope remains stable in dry conditions but fails catastrophically when soil moisture surpasses 80%. Linear models cannot capture these compound tipping points, while Deep Learning models require tens of thousands of real sensor samples that are scarce in disaster management. Random Forest handles non-linear interactions reliably without overfitting on small-to-medium geotechnical datasets.

**Q2: What is the physical basis of the features used?**
> *Answer:* The model is grounded in classical geotechnical slope stability and Caine's (1980) rainfall intensity-duration thresholds:
> 1. **Rainfall (24h/72h)**: Drives groundwater table elevation and positive pore-water pressure, reducing the effective normal stress ($\sigma' = \sigma - u$).
> 2. **Soil Moisture**: Measures soil saturation approaching the liquid limit where shear strength drops drastically.
> 3. **Slope Angle**: Determines the gravitational driving shear stress ($\tau = \gamma h \sin\beta\cos\beta$).
> 4. **Ground Vibration**: Accounts for horizontal seismic or heavy traffic accelerations that destabilize active shear planes.

**Q3: How does the system handle communication in remote Himalayan areas with poor internet?**
> *Answer:* The architecture supports edge telemetry queuing (via microcontrollers over LoRaWAN or satellite SMS). When connectivity resumes, packets are pushed in bulk to the REST API endpoint (`/api/readings/`), which processes and logs them chronologically.

---

### Tech Stack
- **Framework**: Python 3, Django 5.1
- **Machine Learning**: Scikit-Learn 1.9, NumPy, Joblib
- **Geospatial & Visuals**: Leaflet.js, OpenStreetMap, Chart.js 4.4, Bootstrap 5.3
- **Data & APIs**: Open-Meteo REST API, SQLite / PostgreSQL
