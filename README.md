# 🚚 RouteSense — AI-Powered Logistics Route Intelligence

**RouteSense** is a full-stack logistics operations dashboard built with Streamlit. It solves multi-vehicle delivery routing using Google OR-Tools VRP, visualizes live fleet status on interactive maps, predicts delay risk using time-of-day AI scoring, and delivers voice-guided driver briefings in English, Hindi, and Tamil.

> Built as a prototype for real-world last-mile delivery operations.

---

## ✨ Features at a Glance

| Feature | Description |
|---|---|
| 🗺️ **Multi-driver Route Maps** | Color-coded Folium maps for every driver, combined and individual |
| ⚡ **VRP Optimization** | Google OR-Tools with capacity constraints + Guided Local Search |
| 🧠 **AI Delay Prediction** | Risk scoring (0–100) based on time of day, distance, and stop count |
| 🔥 **Risk Heatmap** | Corridor-level congestion heatmap across all delivery zones |
| 🎙️ **Voice Announcements** | Browser TTS in English / हिंदी / தமிழ் with auto-alerts |
| ⏰ **Scheduled Auto-Alerts** | Fires automatically when a delivery time is 2 min away or overdue |
| 📤 **CSV Upload & Apply** | Upload your own deliveries + fleet CSVs and re-optimise instantly |
| ⚖️ **Route Comparison** | Side-by-side maps: unoptimised vs VRP, with distance/fuel/CO₂ savings |
| 📊 **Analytics Dashboard** | Charts for distance, demand, fuel, CO₂, and capacity utilisation |
| 🌙 / ☀️ **Dark / Light Theme** | Glassmorphism dark mode + clean light mode, toggleable per session |

---

## 🖥️ Live Demo

**[routesense.onrender.com](https://routesense-xeit.onrender.com)**

---

## 🗂️ Project Structure

```
logistics_route_optimization/
│
├── app.py                  # Main Streamlit app — all UI, logic & VRP calls
├── requirements.txt
├── render.yaml             # Render.com deployment config
│
├── data/
│   ├── deliveries.csv      # Default delivery stops (Chennai sample data)
│   ├── fleet.csv           # Default fleet / driver roster
│   └── generate_data.py    # Script to regenerate sample CSVs
│
├── modules/
│   ├── data_loader.py      # CSV loading helpers
│   ├── vrp_optimizer.py    # OR-Tools VRP wrapper
│   ├── clustering.py       # Stop clustering utilities
│   ├── traffic_simulator.py
│   └── learning_engine.py
│
├── dashboard/
│   ├── map_view.py         # Folium map helpers
│   └── metrics.py          # Streamlit metric card helpers
│
└── utils/
    └── distance_matrix.py  # Haversine distance matrix builder
```

---

## 🚀 Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/SRIJAA12/routesense.git
cd routesense
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Start the app**
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## 📋 CSV Data Format

### `data/deliveries.csv`

| Column | Required | Description |
|---|---|---|
| `id` | ✅ | Unique stop ID (`0` = depot) |
| `location` | ✅ | Place name |
| `lat` | ✅ | Latitude (decimal degrees) |
| `lon` | ✅ | Longitude (decimal degrees) |
| `demand` | Optional | Load units for capacity planning |
| `driver_id` | Optional | Pre-assign a stop to a specific driver |
| `est_delivery_time` | Optional | Scheduled delivery time (HH:MM) — enables auto voice alerts |

### `data/fleet.csv`

| Column | Required | Description |
|---|---|---|
| `vehicle_id` | ✅ | Driver / vehicle ID (e.g. `D1`) |
| `capacity` | ✅ | Max load units this vehicle can carry |
| `driver_name` | Optional | Full name shown on dashboard |
| `driver_phone` | Optional | Phone number shown on Fleet tab |
| `area` | Optional | Assigned delivery zone |

> Download ready-to-fill templates directly from the **📤 Upload Data** tab inside the app.

---

## 🧭 How to Use

1. **Open the app** → defaults load the Chennai sample dataset with 3 drivers and 11 stops.
2. **Upload your own data** → go to **📤 Upload Data**, download the templates, fill them in, upload both CSVs, and click **Apply & Optimise**.
3. **View routes** → **📍 Operations** tab shows all drivers on a combined map + individual driver maps with stop tables.
4. **Check AI insights** → **🧠 AI Insights** shows delay risk gauge, heatmap, ETA predictions, and fleet recommendations.
5. **Driver mode** → switch the role to **Driver** in the sidebar to see per-driver dashboards with voice buttons.
6. **Refresh / re-optimise** → click **⚡ Optimise Routes** in the sidebar at any time.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Framework | [Streamlit](https://streamlit.io) |
| Route Optimization | [Google OR-Tools](https://developers.google.com/optimization) — VRP with capacity constraints |
| Interactive Maps | [Folium](https://python-visualization.github.io/folium/) + streamlit-folium |
| Charts | [Plotly](https://plotly.com/python/) Express & Graph Objects |
| Data Processing | Pandas, NumPy |
| Voice | Browser Web Speech API (`SpeechSynthesisUtterance`) |
| Styling | Custom CSS — Inter font, glassmorphism cards, gradient backgrounds |
| Deployment | [Render](https://render.com) |

---

## ⚙️ Optimization Engine

- **Algorithm:** Path Cheapest Arc (first solution) + Guided Local Search metaheuristic (2–3 s time limit)
- **Distance metric:** Haversine formula for real-world km between lat/lon pairs
- **Capacity constraints:** Each vehicle's max load is enforced; solver retries without capacity if infeasible
- **ETA model:** 20 km/h during peak hours (08–10, 17–20), 30 km/h otherwise, +5 min service time per stop
- **CO₂ estimate:** 0.21 kg per km | **Fuel estimate:** 0.18 L per km

---

## 🌐 Deployment (Render)

The app is deployed via [render.yaml](render.yaml). To deploy your own instance:

1. Fork this repo
2. Create a new **Web Service** on [render.com](https://render.com)
3. Connect your fork — Render auto-detects `render.yaml`
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

---

## 📸 Screenshots

| Dark Mode Dashboard | Operations Map |
|---|---|
| Admin KPI cards with glassmorphism styling | Color-coded multi-driver route overview |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Made with ❤️ for logistics intelligence.*
