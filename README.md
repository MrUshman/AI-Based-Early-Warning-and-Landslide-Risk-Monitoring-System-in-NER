# AI-Based Early Warning and Landslide Risk Monitoring System in NER
### A Geotechnical Early Warning & Disaster Risk Reduction Platform for the North Eastern Region of India

[![Django](https://img.shields.io/badge/Django-5.x%20%7C%206.x-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11%2B%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Leaflet](https://img.shields.io/badge/Leaflet-GIS%20Mapping-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-Data%20Visualization-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)

---

## 📌 Executive Summary & Regional Context
The **North Eastern Region (NER) of India** (Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, and Tripura) is one of the most landslide-susceptible zones on Earth. The combination of geologically young, steep Himalayan mountains, intense monsoon precipitation (June to September), high seismic activity, and vital cut-slope highways (e.g., NH-10, NH-6, NH-29) means that slope failures frequently cut off entire states and districts.

This system provides an **explainable, transparent early warning and risk monitoring web portal** designed for district administrations, highway maintenance agencies (BRO/NHIDCL), emergency responders (NDRF/SDRF), and the travelling public.

---

## 🌟 Key Features

1. **Explainable AI Risk Engine (0–100 Scale):**
   - Pure, deterministic, verifiable mathematical function:
     $$\text{Total Score} = \text{Rainfall (40)} + \text{Soil Moisture (25)} + \text{Slope Angle (20)} + \text{Ground Vibration (15)}$$
   - No opaque black boxes: every score can be checked by hand by a District Collector or Viva Examiner.

2. **Automated Alert Pipeline:**
   - Any reading scoring **$\ge$ 50.0** immediately generates an official public alert with plain-language operational directives.
   - Distinct alert lifecycle: `ACTIVE` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `CLOSED`, with auditable officer timestamps in **Indian Standard Time (IST)**.

3. **Multi-Role Access Control (RBAC):**
   - **Public Visitor:** No login required. View live dashboard, interactive Leaflet GIS map, 12 slope dossiers, active alerts, incident records, and safety guidance.
   - **Field Officer / Operator (`field_operator`):** Log in to enter sensor readings (with live risk preview) and report field incidents.
   - **District Admin / DDMA Officer (`ddma_officer`):** Acknowledge and close active alerts with mandatory operational action notes, triage command queue, and inspect audit logs.
   - **Super Admin (`admin`):** Full control over locations, users, groups, and Django administration console.

4. **Executive UI/UX Design System:**
   - **Accessible Risk Badging:** Strictly follows the **Colour + Icon + Text + Numeric Score** design rule for color-blind users and bright sunlight:
     - 🟢 **LOW (0–24):** `#16A34A` + Check Icon
     - 🟡 **MODERATE (25–49):** `#CA8A04` + Watch/Eye Icon
     - 🟠 **HIGH (50–74):** `#EA580C` + Warning Triangle Icon
     - 🔴 **CRITICAL (75–100):** `#DC2626` + Siren/Octagon Icon
   - **Interactive Leaflet.js GIS Map:** Color-coded pins for all 12 monitoring locations across the 8 NER states.
   - **Chart.js Visualizations:** Dynamic multi-observation hazard trend lines for individual slopes.
   - **Low-Bandwidth & Mobile-First:** Server-rendered Django templates with 44px+ tap targets for field smartphones on weak 3G/4G connections.
   - **Emergency Helpline 112:** One-click instant dial banner for travelers and residents.
   - **1-Click Demo Login:** Instant auto-fill buttons on the login screen for seamless examiner demonstration.

---

## 🗺️ Monitored Locations Across 8 NER States

| # | Location Name | State | District / Sector | Lat, Long | Default Slope | Critical Significance |
|---|---------------|-------|-------------------|-----------|---------------|-----------------------|
| 1 | **Sonapur Tunnel Area, NH-6** | Meghalaya | East Jaintia Hills | 25.1092° N, 92.3614° E | 45° | Vital tunnel bottleneck connecting Barak Valley, Mizoram & Tripura |
| 2 | **NH-10 km 32** | Sikkim | Pakyong / Kalimpong border | 27.2038° N, 88.5132° E | 42° | Main lifeline corridor connecting Gangtok with Siliguri |
| 3 | **Gangtok Town Slope** | Sikkim | East Sikkim | 27.3389° N, 88.6065° E | 36° | Urban slope directly threatening capital wards & bazaars |
| 4 | **Shillong-Dawki Road** | Meghalaya | East Khasi Hills | 25.3854° N, 91.8842° E | 38° | Tourist & international trade corridor with deep river gorges |
| 5 | **Aizawl-Hunthar Veng** | Mizoram | Aizawl | 23.7428° N, 92.7176° E | 39° | Historic active sinking zone threatening main western city access |
| 6 | **Kohima NH-29** | Nagaland | Kohima | 25.6701° N, 94.1077° E | 41° | Primary highway sustaining supply lines into Nagaland & Manipur |
| 7 | **Itanagar NH-415** | Arunachal Pradesh | Papum Pare | 27.0979° N, 93.6166° E | 35° | Capital road corridor subject to torrential runoff & toe erosion |
| 8 | **Bomdila Pass Road** | Arunachal Pradesh | West Kameng | 27.2645° N, 92.4227° E | 44° | High-altitude strategic military route to Tawang (8,500 ft) |
| 9 | **Ukhrul Road Slope** | Manipur | Ukhrul | 25.1161° N, 94.3622° E | 37° | District hill lifeline prone to monsoon isolation mudslides |
| 10 | **Guwahati-Fancy Bazar Hill** | Assam | Kamrup Metropolitan | 26.1852° N, 91.7458° E | 32° | Dense urban hillside with steep cuts above marketplace |
| 11 | **Haflong-New Haflong** | Assam | Dima Hasao | 25.1764° N, 93.0238° E | 43° | Severe instability zone prone to catastrophic rail & road washouts |
| 12 | **Agartala-Assam Rifles Slope** | Tripura | West Tripura | 23.8438° N, 91.2868° E | 30° | Capital ridge slope prone to gully erosion during cloudbursts |

---

## 🧮 Explainable AI Risk Formula & Worked Example

### Mathematical Breakdown
1. **Rainfall Factor (Max 40 pts):**
   - 24-hour intense rain: Scaled up to 150 mm (60% weight = max 24 pts)
   - 72-hour antecedent rain: Scaled up to 300 mm (40% weight = max 16 pts)
2. **Soil Moisture Factor (Max 25 pts):**
   - Volumetric saturation: 0% to 100% $\rightarrow$ 0 to 25 pts
3. **Slope Angle Factor (Max 20 pts):**
   - Baseline slope steepness: 0° to 50° mapped to 0 to 20 pts
4. **Ground Vibration Factor (Max 15 pts):**
   - Peak Particle Velocity (PPV): 0.0 to 10.0 mm/s mapped to 0 to 15 pts

### The Benchmark Worked Example (Sonapur Tunnel Area, NH-6)
- **Rainfall:** 125.0 mm in 24h + 262.5 mm in 72h $\rightarrow$ **34.0 / 40 pts**
- **Soil Moisture:** 88.0% saturation $\rightarrow$ **22.0 / 25 pts**
- **Slope Angle:** 42.5° $\rightarrow$ **17.0 / 20 pts**
- **Ground Vibration:** 6.0 mm/s $\rightarrow$ **9.0 / 15 pts**
- **Total Calculation:** $34.0 + 22.0 + 17.0 + 9.0 = \mathbf{82.0 / 100}$
- **Outcome:** **CRITICAL RISK** $\rightarrow$ Automatic alert generated, triggering road closure recommendations and NDRF standby units.

---

## 🏛️ Inter-Agency Operational Chain in India

```
  [IMD] Rainfall Telemetry & Forecasts
               │
               ▼
  [Field Telemetry / Sensors] ──> [Explainable AI Engine] ──> High/Critical Risk?
                                                                   │
                                                                   ▼
                                                       [Automated Public Alert]
                                                                   │
               ┌───────────────────────────────────────────────────┼──────────────────────────────┐
               ▼                                                   ▼                              ▼
    [DDMA District Admin]                                   [BRO / NHIDCL]                 [NDRF / SDRF]
    Acknowledge & Direct Action                             Traffic Halts & Heavy Plant    Preposition Rescue Units
```

---

## 🔑 Demo & Examiner Credentials

Use the **1-Click Auto-Fill** buttons on the `/accounts/login/` page:

| Role | Username | Password | Key Permissions |
|------|----------|----------|-----------------|
| **Super Admin** | `admin` | `Admin@123` | Full administrative control, location CRUD, user management, Django admin |
| **DDMA Officer** | `ddma_officer` | `Officer@123` | Acknowledge alerts, close alerts, view officer queue, report incidents |
| **Field Operator** | `field_operator` | `Operator@123` | Enter sensor readings, view assigned slopes, report suspected slides |
| **Public Visitor** | *(No login)* | *(None)* | Read-only access to dashboard, map, 12 slopes, alerts, incidents, safety SOPs |

---

## 🚀 Quickstart & Installation Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/MrUshman/AI-Based-Early-Warning-and-Landslide-Risk-Monitoring-System-in-NER.git
cd AI-Based-Early-Warning-and-Landslide-Risk-Monitoring-System-in-NER
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py migrate
```

### 5. Seed the Complete Dataset (All 12 Locations, Readings & Accounts)
```bash
python manage.py seed_data
```

### 6. Run Automated Test Suite
```bash
python manage.py test
```
*Executes all 9 unit and integration tests (T1 through T9) verifying mathematical calculations, boundary conditions (24/25, 49/50, 74/75), role permissions, and alert triggers.*

### 7. Launch Development Server
```bash
python manage.py runserver
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🧪 Testing Specification (T1 – T9)

| Test ID | Test Target | Inputs | Expected Result | Status |
|---------|-------------|--------|-----------------|:------:|
| **T1** | Worked Example | $34 + 22 + 17 + 9$ | Total $82.0$, Level `CRITICAL` | ✅ Pass |
| **T2** | Top of Moderate Boundary | Factors summing to $49.0$ | Level `MODERATE`, No alert created | ✅ Pass |
| **T3** | Start of High Boundary | Factors summing to $50.0$ | Level `HIGH`, Auto alert created | ✅ Pass |
| **T4** | Start of Critical Boundary | Factors summing to $75.0$ | Level `CRITICAL`, Auto alert created | ✅ Pass |
| **T5** | Low Reading Check | Factors summing to $10.0$ | Level `LOW`, Alert count unchanged | ✅ Pass |
| **T6** | Form Validation Boundary | Rainfall $-10\text{mm}$, Soil $140\%$ | Form rejected with inline error | ✅ Pass |
| **T7** | Public View Protection | Anonymous access to `/readings/add/` | Redirected to `/accounts/login/` | ✅ Pass |
| **T8** | Role Permission Gate | Field Operator attempts to acknowledge alert | `403 Forbidden` response | ✅ Pass |
| **T9** | Audit Timestamp Trail | DDMA officer acknowledges alert | Status `ACKNOWLEDGED`, officer saved | ✅ Pass |

---

## 🎓 Academic Viva Questions & Answers

1. **Why weights 40 - 25 - 20 - 15?**
   - *Rainfall (40):* Monsoon rainfall is the recognized primary trigger of catastrophic slope failures in the Himalayas.
   - *Soil Moisture (25):* Saturated soil loses internal friction and develops high pore-water pressure, leading to liquefaction.
   - *Slope Angle (20):* Geometrical baseline; steeper slopes ($>35^\circ$) have higher static shear stress.
   - *Ground Vibration (15):* Critical precursor reflecting micro-tremors, heavy transport resonance, or creeping shear surfaces.

2. **Why explainable scoring instead of Deep Learning / Random Forest directly?**
   - In disaster response and civil administration, authorities cannot justify closing a national highway or evacuating families based on an opaque black-box neural network. Officers must be able to defend their actions before state authorities. The formula provides 100% auditability.

3. **What is the difference between Version 1 and Future Scope?**
   - *Version 1 (Current):* Operational web portal with manual/seeded telemetry, transparent explainable AI scoring engine, full RBAC response chain, Leaflet GIS mapping, and Chart.js trends.
   - *Future Scope:* Live hardware IoT rain gauge and piezometer integrations, automatic IMD weather API webhook ingestion, SMS/WhatsApp broadcast alerts, and machine-learning models trained on accumulated multi-season data.

---

## 📜 License
Developed for educational research and disaster risk reduction demonstration in the North Eastern Region of India.
