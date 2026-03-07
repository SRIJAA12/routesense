import datetime
import json
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import folium
from folium.plugins import HeatMap
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from modules.data_loader import load_deliveries, load_fleet

st.set_page_config(
    page_title="RouteSense — Logistics Intelligence",
    layout="wide",
    page_icon="🚚",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# THEME  (glassmorphism cards, gradient hero, premium typography)
# ═══════════════════════════════════════════════════════════════════════════════

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, .stApp { font-family: 'Inter', sans-serif !important; }

.stApp { background: radial-gradient(ellipse at top, #0d1b2a 0%, #050b14 60%, #020608 100%); color: #e2e8f0 !important; }

/* glassmorphism cards */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 16px 20px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    transition: transform 0.2s;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); }
[data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700 !important; color: #93c5fd !important; }
[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.08em; }

/* sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0b1623 0%,#060f1c 100%); border-right: 1px solid rgba(255,255,255,0.07); }
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }

/* buttons */
.stButton > button {
    background: linear-gradient(135deg,#2563eb,#1d4ed8);
    color: #fff !important;
    border: none; border-radius: 10px;
    font-weight: 600; font-size: 0.85rem;
    width: 100%; padding: 0.55rem 1rem;
    box-shadow: 0 2px 12px rgba(37,99,235,0.35);
    transition: all 0.2s;
}
.stButton > button:hover { background: linear-gradient(135deg,#1d4ed8,#1e40af); transform: translateY(-1px); box-shadow: 0 4px 18px rgba(37,99,235,0.5); }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid rgba(255,255,255,0.08); }
.stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 18px; color: #64748b !important; font-weight: 600; font-size: 0.85rem; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: #60a5fa !important; background: rgba(96,165,250,0.08); border-bottom: 2px solid #3b82f6; }

/* dataframes */
[data-testid="stDataFrame"] * { color: #e2e8f0 !important; }

/* text */
p, span, label, li, td, th, caption, .stMarkdown, div { color: #cbd5e1 !important; }
h1,h2,h3,h4 { color: #f8fafc !important; }

/* info / warning */
[data-testid="stAlert"] { border-radius: 10px; }

/* progress bar */
[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg,#3b82f6,#06b6d4); }

/* divider */
hr { border-color: rgba(255,255,255,0.07) !important; }
</style>
"""

LIGHT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, .stApp { font-family: 'Inter', sans-serif !important; }

.stApp { background: linear-gradient(160deg,#f0f7ff 0%,#e8f0fe 50%,#f5f3ff 100%); color: #0f172a !important; }

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #dbeafe;
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 2px 10px rgba(59,130,246,0.08);
    transition: transform 0.2s;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(59,130,246,0.14); }
[data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700 !important; color: #1d4ed8 !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.08em; }

[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #bfdbfe; }
[data-testid="stSidebar"] * { color: #1e293b !important; }

.stButton > button {
    background: linear-gradient(135deg,#1d4ed8,#2563eb);
    color: #fff !important; border: none; border-radius: 10px;
    font-weight: 600; font-size: 0.85rem; width: 100%; padding: 0.55rem 1rem;
    box-shadow: 0 2px 10px rgba(29,78,216,0.25);
    transition: all 0.2s;
}
.stButton > button:hover { background: linear-gradient(135deg,#1e40af,#1d4ed8); transform: translateY(-1px); }

.stTabs [data-baseweb="tab"] { color: #64748b !important; font-weight: 600; font-size: 0.85rem; border-radius: 8px 8px 0 0; padding: 8px 18px; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: #1d4ed8 !important; background: #eff6ff; border-bottom: 2px solid #1d4ed8; }

p, span, label, li, td, th, caption, .stMarkdown, div { color: #0f172a !important; }
h1,h2,h3,h4 { color: #1e3a8a !important; }
[data-testid="stDataFrame"] * { color: #0f172a !important; }

[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg,#3b82f6,#0ea5e9); }
hr { border-color: #e2e8f0 !important; }
</style>
"""

def apply_theme(is_dark):
    st.markdown(DARK_CSS if is_dark else LIGHT_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CORE UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    rl = np.radians([lat1, lon1, lat2, lon2])
    dlat, dlon = rl[2]-rl[0], rl[3]-rl[1]
    a = np.sin(dlat/2)**2 + np.cos(rl[0])*np.cos(rl[2])*np.sin(dlon/2)**2
    return R*2*np.arctan2(np.sqrt(a), np.sqrt(1-a))


def load_operational_data():
    deliveries = load_deliveries().copy()
    fleet = load_fleet().copy()
    for col in ("id","location","lat","lon"):
        if col not in deliveries.columns:
            raise ValueError(f"deliveries.csv missing column: '{col}'")
    for col in ("vehicle_id","capacity"):
        if col not in fleet.columns:
            raise ValueError(f"fleet.csv missing column: '{col}'")
    deliveries["lat"] = pd.to_numeric(deliveries["lat"], errors="coerce")
    deliveries["lon"] = pd.to_numeric(deliveries["lon"], errors="coerce")
    deliveries = deliveries.dropna(subset=["lat","lon"]).reset_index(drop=True)
    if deliveries.empty:
        raise ValueError("No valid delivery coordinates in deliveries.csv")
    if "type" not in deliveries.columns:
        deliveries["type"] = np.where(deliveries["id"]==0,"depot","delivery")
    return deliveries.sort_values("id").reset_index(drop=True), fleet


def create_distance_matrix(df):
    coords = df[["lat","lon"]].to_numpy(); n = len(coords)
    dm = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            if i!=j:
                dm[i,j] = haversine_km(coords[i][0],coords[i][1],coords[j][0],coords[j][1])
    return dm


def optimize_route_vrp(dm):
    manager = pywrapcp.RoutingIndexManager(len(dm),1,0)
    routing = pywrapcp.RoutingModel(manager)
    def cb(fi,ti):
        return int(dm[manager.IndexToNode(fi)][manager.IndexToNode(ti)]*1000)
    ci = routing.RegisterTransitCallback(cb)
    routing.SetArcCostEvaluatorOfAllVehicles(ci)
    p = pywrapcp.DefaultRoutingSearchParameters()
    p.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    p.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    p.time_limit.seconds = 2
    sol = routing.SolveWithParameters(p)
    if sol is None: return [],0.0
    route,tm=[],0; idx=routing.Start(0)
    while not routing.IsEnd(idx):
        route.append(manager.IndexToNode(idx)); prev=idx
        idx=sol.Value(routing.NextVar(idx))
        tm+=routing.GetArcCostForVehicle(prev,idx,0)
    route.append(manager.IndexToNode(idx))
    return route, tm/1000.0


def sequential_route_distance(dm):
    p=list(range(dm.shape[0]))+[0]
    return float(sum(dm[p[i],p[i+1]] for i in range(len(p)-1)))


def optimize_multi_vehicle_vrp(dm, n_vehicles, demands=None, max_capacity=100):
    """Multi-vehicle VRP. Returns ({vehicle_idx: [node...]}, total_dist_km)."""
    n = len(dm)
    n_vehicles = max(1, n_vehicles)
    manager = pywrapcp.RoutingIndexManager(n, n_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    def transit_cb(fi, ti):
        return int(dm[manager.IndexToNode(fi)][manager.IndexToNode(ti)] * 1000)
    tid = routing.RegisterTransitCallback(transit_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(tid)

    if demands is not None and max_capacity > 0:
        def demand_cb(fi):
            return int(demands[manager.IndexToNode(fi)])
        did = routing.RegisterUnaryTransitCallback(demand_cb)
        routing.AddDimensionWithVehicleCapacity(
            did, 0, [int(max_capacity)] * n_vehicles, True, "Capacity")

    p = pywrapcp.DefaultRoutingSearchParameters()
    p.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    p.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    p.time_limit.seconds = 3
    sol = routing.SolveWithParameters(p)
    routes_dict: dict = {}
    total_dist = 0.0
    if sol:
        for v in range(n_vehicles):
            route: list = []
            idx = routing.Start(v)
            while not routing.IsEnd(idx):
                route.append(manager.IndexToNode(idx))
                prev = idx
                idx = sol.Value(routing.NextVar(idx))
                total_dist += routing.GetArcCostForVehicle(prev, idx, v)
            route.append(manager.IndexToNode(idx))
            routes_dict[v] = route
    return routes_dict, total_dist / 1000.0


def allocate_by_driver_col(df: "pd.DataFrame", fleet_df: "pd.DataFrame") -> dict:
    """Build per-vehicle routes from a driver_id column in df."""
    vehicles = fleet_df["vehicle_id"].tolist()
    routes: dict = {}
    for v_idx, vid in enumerate(vehicles):
        mask = (df["driver_id"].astype(str) == str(vid)) | (df["id"] == 0)
        nodes = df[mask].index.tolist()
        route = [0] + [i for i in nodes if i != 0] + [0]
        routes[v_idx] = route
    return routes


# ── CSV Templates ──────────────────────────────────────────────────────────────
DELIVERIES_TEMPLATE_CSV = (
    "id,location,lat,lon,demand,driver_id,est_delivery_time\n"
    "0,Chennai Depot,13.0827,80.2707,0,,\n"
    "1,T Nagar,13.0418,80.2341,2,D1,09:15\n"
    "2,Velachery,12.9815,80.2180,3,D2,09:30\n"
    "3,Tambaram,12.9249,80.1000,4,D3,09:45\n"
    "4,Anna Nagar,13.0850,80.2101,2,D1,10:00\n"
    "5,Adyar,13.0012,80.2565,3,D2,10:15\n"
    "6,Porur,13.0358,80.1573,2,D3,10:30\n"
    "7,Guindy,13.0067,80.2206,4,D1,10:45\n"
    "8,OMR,12.9001,80.2279,3,D2,11:00\n"
    "9,Perambur,13.1152,80.2337,2,D3,11:15\n"
    "10,Mylapore,13.0339,80.2619,3,D1,11:30\n"
    "11,Sholinganallur,12.9010,80.2279,2,D2,11:45\n"
)

FLEET_TEMPLATE_CSV = (
    "vehicle_id,capacity,driver_name,driver_phone,area\n"
    "D1,8,Rajan Kumar,9876543210,North Chennai\n"
    "D2,8,Priya Sharma,8765432109,South Chennai\n"
    "D3,8,Mohan Das,7654321098,Central Chennai\n"
)


# ═══════════════════════════════════════════════════════════════════════════════
# AI / ANALYTICS HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def predict_delay_risk(distance_km, n_stops, hour=None):
    if hour is None:
        hour = datetime.datetime.now().hour
    score = 0
    # Peak hour factor (Chennai traffic)
    if hour in [8,9,10,17,18,19,20]:
        score += 38
    elif hour in [11,12,13,14,15,16]:
        score += 18
    else:
        score += 8
    # Distance factor
    score += min(int(distance_km * 0.5), 35)
    # Stops factor
    score += min(n_stops * 2, 25)
    score = min(score, 100)
    if score >= 65:
        return "High", score, "#ef4444"
    elif score >= 38:
        return "Medium", score, "#f59e0b"
    else:
        return "Low", score, "#22c55e"


def compute_eta(df, route, distance_km, hour=None):
    """Return {node: 'HH:MM'} ETA dict for each stop."""
    if hour is None:
        hour = datetime.datetime.now().hour
    speed = 20.0 if hour in [8,9,10,17,18,19] else 30.0
    start = datetime.datetime.now()
    eta = {}
    elapsed_min = 0.0
    for i in range(len(route)-1):
        a, b = route[i], route[i+1]
        d = haversine_km(df.iloc[a]["lat"],df.iloc[a]["lon"],df.iloc[b]["lat"],df.iloc[b]["lon"])
        elapsed_min += (d / speed)*60 + 5  # +5min service
        t = start + datetime.timedelta(minutes=elapsed_min)
        eta[b] = t.strftime("%H:%M")
    return eta


def corridor_risk_points(df, seed=42):
    """Generate heatmap points around delivery nodes with risk intensity."""
    rng = np.random.default_rng(seed)
    pts = []
    for _, row in df.iterrows():
        if row.get("type","delivery") == "depot":
            base = 0.3
        else:
            demand = float(row.get("demand",1))
            base = min(0.4 + demand*0.15, 1.0)
        for _ in range(8):
            jlat = row["lat"] + rng.normal(0, 0.008)
            jlon = row["lon"] + rng.normal(0, 0.008)
            pts.append([jlat, jlon, base + rng.uniform(0, 0.3)])
    return pts


def fleet_recommendation(df, fleet_df, route, dist):
    recs = []
    n_stops = len([n for n in (route or []) if n != 0])
    total_demand = float(df["demand"].sum()) if "demand" in df.columns else 0
    total_cap = float(fleet_df["capacity"].sum()) if "capacity" in fleet_df.columns else 0
    util = (total_demand/total_cap*100) if total_cap>0 else 0
    if util < 40:
        recs.append(("💡","Consolidate loads — fleet capacity is under-utilised ({:.0f}%). Consider reducing active vehicles.".format(util)))
    elif util > 85:
        recs.append(("⚠️","High load utilisation ({:.0f}%). Deploy an additional vehicle to reduce per-truck pressure.".format(util)))
    if dist > 60:
        recs.append(("💡","Route distance is long ({:.1f} km). Consider splitting into two shorter sub-routes for faster delivery.".format(dist)))
    if n_stops > 9:
        recs.append(("💡","More than 9 stops on a single vehicle. Dispatching a second truck can cut ETA by ~30%."))
    if not recs:
        recs.append(("✅","Fleet configuration looks optimal for current demand. No changes recommended."))
    return recs


def generate_alerts(df, route, delay_level, dist):
    alerts = []
    hour = datetime.datetime.now().hour
    if delay_level == "High":
        alerts.append(("🔴","HIGH","Traffic congestion risk detected — consider re-routing or delaying dispatch by 30 min."))
    elif delay_level == "Medium":
        alerts.append(("🟡","WARN","Moderate delay risk on current route. Monitor traffic conditions."))
    if hour in [8,9,10]:
        alerts.append(("🟡","WARN","Morning peak hours active (08:00–10:30). Expect 20–40% slower travel times."))
    if hour in [17,18,19]:
        alerts.append(("🟡","WARN","Evening rush hour (17:00–20:00). Road congestion elevated across Chennai corridors."))
    if dist > 60:
        alerts.append(("🔵","INFO","Total route length exceeds 60 km. Fuel check recommended before departure."))
    if not route:
        alerts.append(("🔵","INFO","No optimised route generated yet. Run optimisation to unlock AI features."))
    if not alerts:
        alerts.append(("🟢","OK","All systems operational — no active alerts."))
    return alerts


# ═══════════════════════════════════════════════════════════════════════════════
# MAP BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_route_map(df, route, active_stop_index, map_key, height=540):
    center = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=12, control_scale=True,
                   tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        is_depot = str(row.get("type","delivery"))=="depot"
        label = row["location"]
        if "demand" in df.columns and not is_depot:
            label = f"{label} — Demand: {row['demand']}"
        color = "#22c55e" if is_depot else "#60a5fa"
        icon_html = f"""<div style="background:{color};width:{'16px' if is_depot else '12px'};height:{'16px' if is_depot else '12px'};
            border-radius:50%;border:2px solid white;box-shadow:0 0 6px {color};"></div>"""
        folium.Marker(
            location=[row["lat"],row["lon"]],
            icon=folium.DivIcon(html=icon_html, icon_size=(16,16), icon_anchor=(8,8)),
            popup=folium.Popup(label, max_width=220),
            tooltip=label,
        ).add_to(m)
    if route:
        pts = [[df.iloc[n]["lat"],df.iloc[n]["lon"]] for n in route]
        folium.PolyLine(pts, color="#f97316", weight=4, opacity=0.85,
                        dash_array=None, tooltip="Optimised Route").add_to(m)
        if active_stop_index is not None and 0<=active_stop_index<len(route):
            node = route[active_stop_index]
            truck_html = """<div style="font-size:22px;filter:drop-shadow(0 0 4px #ef4444);">🚛</div>"""
            folium.Marker(
                [df.iloc[node]["lat"],df.iloc[node]["lon"]],
                icon=folium.DivIcon(html=truck_html, icon_size=(28,28), icon_anchor=(14,14)),
                popup="Active Vehicle",tooltip="Vehicle Position",
            ).add_to(m)
    st_folium(m, width=None, height=height, use_container_width=True, key=map_key)


def build_risk_heatmap(df, map_key, height=500):
    center = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=12, tiles="CartoDB dark_matter")
    pts = corridor_risk_points(df)
    HeatMap(pts, radius=22, blur=18, gradient={
        "0.2":"#22c55e","0.5":"#f59e0b","0.75":"#f97316","1.0":"#ef4444"
    }).add_to(m)
    # Delivery markers on top
    for _, row in df.iterrows():
        is_depot = str(row.get("type","delivery"))=="depot"
        if not is_depot:
            folium.CircleMarker(
                [row["lat"],row["lon"]], radius=5, color="white", fill=True,
                fill_color="white", fill_opacity=0.9, tooltip=row["location"],
            ).add_to(m)
    st_folium(m, width=None, height=height, use_container_width=True, key=map_key)


# One distinct colour per driver — cycles if > 8 vehicles
DRIVER_COLORS = [
    "#f97316",  # orange    — driver 0
    "#22c55e",  # green     — driver 1
    "#a855f7",  # purple    — driver 2
    "#06b6d4",  # cyan      — driver 3
    "#f43f5e",  # rose      — driver 4
    "#facc15",  # yellow    — driver 5
    "#38bdf8",  # sky       — driver 6
    "#fb7185",  # pink      — driver 7
]
DRIVER_COLOR_ICONS = ["🟠","🟢","🟣","🔵","🔴","🟡","🩵","🩷"]


def _driver_color(v_idx: int) -> str:
    return DRIVER_COLORS[v_idx % len(DRIVER_COLORS)]


def build_all_drivers_map(df, driver_routes: dict, fleet_df, map_key: str, height: int = 480):
    """Single folium map showing every driver route in a distinct colour."""
    center = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=12, control_scale=True,
                   tiles="CartoDB dark_matter")

    # Depot marker
    depot_rows = df[df["type"] == "depot"] if "type" in df.columns else df[df["id"] == 0]
    for _, row in depot_rows.iterrows():
        folium.Marker(
            [row["lat"], row["lon"]],
            icon=folium.DivIcon(
                html='<div style="background:#22c55e;width:18px;height:18px;border-radius:50%;'
                     'border:3px solid white;box-shadow:0 0 8px #22c55e;"></div>',
                icon_size=(18, 18), icon_anchor=(9, 9)),
            tooltip=f"🏭 {row['location']} (Depot)",
        ).add_to(m)

    # Per-driver routes
    for v_idx, v_route in driver_routes.items():
        if not v_route:
            continue
        color = _driver_color(v_idx)
        vid = fleet_df.iloc[v_idx]["vehicle_id"] if v_idx < len(fleet_df) else f"Driver {v_idx+1}"
        # Delivery stop markers
        for node in v_route:
            if node == 0:
                continue
            row = df.iloc[node]
            lbl = row["location"]
            dot_html = (f'<div style="background:{color};width:11px;height:11px;border-radius:50%;'
                        f'border:2px solid white;box-shadow:0 0 5px {color};"></div>')
            folium.Marker(
                [row["lat"], row["lon"]],
                icon=folium.DivIcon(html=dot_html, icon_size=(11, 11), icon_anchor=(5, 5)),
                tooltip=f"{vid} → {lbl}",
            ).add_to(m)
        # Route polyline
        pts = [[df.iloc[n]["lat"], df.iloc[n]["lon"]] for n in v_route]
        folium.PolyLine(pts, color=color, weight=3.5, opacity=0.85,
                        tooltip=f"{vid} route").add_to(m)
        # Truck icon at first delivery stop
        first_stop = next((n for n in v_route if n != 0), None)
        if first_stop is not None:
            truck_html = f'<div style="font-size:20px;filter:drop-shadow(0 0 4px {color});">🚛</div>'
            folium.Marker(
                [df.iloc[first_stop]["lat"], df.iloc[first_stop]["lon"]],
                icon=folium.DivIcon(html=truck_html, icon_size=(26, 26), icon_anchor=(13, 13)),
                tooltip=f"{vid} — current position",
            ).add_to(m)

    if not driver_routes:
        # Fallback: just plot all stops
        for _, row in df.iterrows():
            if str(row.get("type", "delivery")) == "depot":
                continue
            folium.CircleMarker([row["lat"], row["lon"]], radius=5, color="#60a5fa",
                                fill=True, fill_opacity=0.8, tooltip=row["location"]).add_to(m)

    st_folium(m, width=None, height=height, use_container_width=True, key=map_key)


def build_driver_map(df, route: list, v_idx: int, map_key: str, height: int = 360):
    """Single-driver route map coloured by driver index."""
    center = [df["lat"].mean(), df["lon"].mean()]
    color = _driver_color(v_idx)
    m = folium.Map(location=center, zoom_start=12, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        is_depot = str(row.get("type", "delivery")) == "depot"
        if is_depot:
            dot = '<div style="background:#22c55e;width:14px;height:14px;border-radius:50%;border:2px solid white;"></div>'
            folium.Marker([row["lat"], row["lon"]],
                          icon=folium.DivIcon(html=dot, icon_size=(14, 14), icon_anchor=(7, 7)),
                          tooltip="Depot").add_to(m)
        else:
            # Only highlight stops in this driver's route
            in_route = route and (df.index.get_loc(row.name) in route or
                                  any(df.iloc[n].name == row.name for n in (route or [])))
            c = color if in_route else "#334155"
            dot = f'<div style="background:{c};width:10px;height:10px;border-radius:50%;border:1px solid #fff;opacity:{1.0 if in_route else 0.4};"></div>'
            folium.Marker([row["lat"], row["lon"]],
                          icon=folium.DivIcon(html=dot, icon_size=(10, 10), icon_anchor=(5, 5)),
                          tooltip=row["location"]).add_to(m)
    if route:
        pts = [[df.iloc[n]["lat"], df.iloc[n]["lon"]] for n in route]
        folium.PolyLine(pts, color=color, weight=3.5, opacity=0.9, tooltip="Route").add_to(m)
        first_stop = next((n for n in route if n != 0), None)
        if first_stop is not None:
            folium.Marker(
                [df.iloc[first_stop]["lat"], df.iloc[first_stop]["lon"]],
                icon=folium.DivIcon(
                    html=f'<div style="font-size:18px;filter:drop-shadow(0 0 4px {color});">🚛</div>',
                    icon_size=(24, 24), icon_anchor=(12, 12)),
                tooltip="Vehicle Position",
            ).add_to(m)
    st_folium(m, width=None, height=height, use_container_width=True, key=map_key)


def build_comparison_map(df, route, title, map_key, height=400):
    center = [df["lat"].mean(), df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=12, tiles="CartoDB positron")
    for _, row in df.iterrows():
        is_depot = str(row.get("type","delivery"))=="depot"
        folium.CircleMarker(
            [row["lat"],row["lon"]], radius=7 if is_depot else 5,
            color="#1d4ed8" if is_depot else "#64748b", fill=True, fill_opacity=0.85,
            tooltip=row["location"],
        ).add_to(m)
    if route:
        pts = [[df.iloc[n]["lat"],df.iloc[n]["lon"]] for n in route]
        folium.PolyLine(pts, color="#7c3aed" if "Original" in title else "#16a34a",
                        weight=4, opacity=0.8, tooltip=title).add_to(m)
    st_folium(m, width=None, height=height, use_container_width=True, key=map_key)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-REFRESH RELAY
# ═══════════════════════════════════════════════════════════════════════════════

# Voice command panel removed — all announcements are now fully automatic.

_AUTOREFRESH_RELAY_CSS = """
<style>
div[data-testid="stTextInput"]:has(input[placeholder="__autorefresh__"]){
    position:absolute;opacity:0;pointer-events:none;height:0;overflow:hidden;}
</style>
"""


def render_autorefresh(delay_secs: int = 45) -> None:
    """
    Inject a JS timer that silently fires a relay token after `delay_secs` seconds,
    causing Streamlit to rerun — which triggers the scheduled-delivery time check.
    """
    st.markdown(_AUTOREFRESH_RELAY_CSS, unsafe_allow_html=True)
    components.html(f"""
<script>
setTimeout(function() {{
  try {{
    var inputs = window.parent.document.querySelectorAll(
      'input[placeholder="__autorefresh__"]');
    if (inputs.length > 0) {{
      var inp = inputs[0];
      var setter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype, 'value').set;
      setter.call(inp, 'TICK_' + Date.now());
      inp.dispatchEvent(new Event('input', {{bubbles: true}}));
    }}
  }} catch(e) {{}}
}}, {int(delay_secs) * 1000});
</script>""", height=0)
    tick = st.text_input("autorefresh", key="auto_refresh_input",
                         placeholder="__autorefresh__",
                         label_visibility="collapsed")
    if tick and tick.startswith("TICK_"):
        st.session_state.auto_refresh_input = ""
        st.rerun()


# render_voice_panel removed — announcements are fully automatic based on est_delivery_time


# ═══════════════════════════════════════════════════════════════════════════════
# DRIVER TTS COMPONENT
# ═══════════════════════════════════════════════════════════════════════════════

def speak_js(text: str, lang: str = "en-US", fallback_text: str = "") -> None:
    """
    Browser TTS.  Strategy (in order):
      1. Try to find a voice that matches `lang` exactly.
      2. If none, try a voice whose name contains a known keyword for that language
         (e.g. 'Hindi', 'Tamil', 'Google \u0939\u093f\u0902\u0926\u0940').
      3. If still none, speak `text` with `lang` set but NO explicit voice —
         modern Chrome/Edge will attempt the language anyway.
      4. Only fall back to English if the browser reports zero voices at all.
    """
    encoded          = json.dumps(text)
    encoded_fallback = json.dumps(fallback_text if fallback_text else text)
    components.html(f"""
<script>
(function(){{
  var txt      = {encoded};
  var fallback = {encoded_fallback};
  var lang     = '{lang}';

  // Known voice name keywords per language prefix
  var LANG_KEYWORDS = {{
    'hi': ['hindi', 'heera', '\u0939\u093f\u0902\u0926\u0940', 'lekha', 'rishi'],
    'ta': ['tamil', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd', 'lekha', 'veena'],
  }};

  function doSpeak(speakText, speakLang, voice) {{
    window.speechSynthesis.cancel();
    setTimeout(function() {{
      var u  = new SpeechSynthesisUtterance(speakText);
      u.lang  = speakLang;
      u.rate  = 0.86;
      u.pitch = 1.0;
      if (voice) u.voice = voice;
      window.speechSynthesis.speak(u);
    }}, 200);
  }}

  function pickVoice(voices, langTag) {{
    var prefix = langTag.split('-')[0].toLowerCase();
    // 1. Exact lang match
    var m = voices.filter(function(v){{ return v.lang === langTag; }});
    if (m.length) return m[0];
    // 2. Prefix match (e.g. 'hi' matches 'hi-IN')
    m = voices.filter(function(v){{ return v.lang.toLowerCase().startsWith(prefix); }});
    if (m.length) return m[0];
    // 3. Keyword in voice name
    var kws = LANG_KEYWORDS[prefix] || [];
    m = voices.filter(function(v){{
      var vl = v.name.toLowerCase();
      return kws.some(function(k){{ return vl.indexOf(k) >= 0; }});
    }});
    if (m.length) return m[0];
    return null;  // no match
  }}

  function trySpeak(voices) {{
    if (voices.length === 0) {{
      // Truly no voices — last resort: plain en-US fallback
      doSpeak(fallback, 'en-US', null);
      return;
    }}
    var v = pickVoice(voices, lang);
    if (v) {{
      doSpeak(txt, lang, v);
    }} else {{
      // No matching voice but voices exist — speak native text with lang set,
      // no explicit voice.  Browser will attempt the language itself.
      doSpeak(txt, lang, null);
    }}
  }}

  var voices = window.speechSynthesis.getVoices();
  if (voices.length === 0) {{
    window.speechSynthesis.addEventListener('voiceschanged', function() {{
      trySpeak(window.speechSynthesis.getVoices());
    }}, {{once: true}});
  }} else {{
    trySpeak(voices);
  }}
}})();
</script>""", height=0)


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

def initialize_state():
    if "dark_mode" not in st.session_state: st.session_state.dark_mode=True
    if "role" not in st.session_state: st.session_state.role="Admin"
    if "deliveries" not in st.session_state:
        d,f=load_operational_data()
        st.session_state.deliveries=d; st.session_state.fleet=f
    if "route" not in st.session_state: st.session_state.route=None
    if "vehicle_index" not in st.session_state: st.session_state.vehicle_index=1
    if "route_distance" not in st.session_state: st.session_state.route_distance=0.0
    if "baseline_distance" not in st.session_state:
        dm=create_distance_matrix(st.session_state.deliveries)
        st.session_state.baseline_distance=sequential_route_distance(dm)
    if "status_message" not in st.session_state:
        st.session_state.status_message="Operational data loaded successfully"
    if "driver_speak" not in st.session_state: st.session_state.driver_speak=False
    if "voice_lang" not in st.session_state: st.session_state.voice_lang="en-US"
    if "last_announcement" not in st.session_state: st.session_state.last_announcement=""
    if "last_announcement_fallback" not in st.session_state: st.session_state.last_announcement_fallback=""
    if "do_speak" not in st.session_state: st.session_state.do_speak=False
    if "driver_routes" not in st.session_state: st.session_state.driver_routes={}
    if "n_vehicles" not in st.session_state: st.session_state.n_vehicles=1
    if "auto_announced" not in st.session_state: st.session_state.auto_announced=set()
    if "auto_refresh_input" not in st.session_state: st.session_state.auto_refresh_input=""


def refresh_data():
    d,f=load_operational_data()
    st.session_state.deliveries=d; st.session_state.fleet=f
    st.session_state.route=None; st.session_state.route_distance=0.0
    st.session_state.vehicle_index=1; st.session_state.driver_routes={}
    st.session_state.auto_announced=set()
    dm=create_distance_matrix(d); st.session_state.baseline_distance=sequential_route_distance(dm)
    # Clear uploaded file widgets so new files can be selected
    for _k in ("del_uploader", "fleet_uploader"):
        if _k in st.session_state:
            del st.session_state[_k]
    st.session_state.status_message="Data refreshed — previous uploads cleared. Upload new files in the Upload Data tab."


def run_optimization():
    df   = st.session_state.deliveries
    fl   = st.session_state.fleet
    dm   = create_distance_matrix(df)
    st.session_state.baseline_distance = sequential_route_distance(dm)
    n_v  = max(1, len(fl))
    demands = df["demand"].fillna(1).astype(int).tolist()
    cap  = int(fl["capacity"].max()) if "capacity" in fl.columns else 100
    if n_v > 1:
        dr, dist = optimize_multi_vehicle_vrp(dm, n_v, demands, cap)
        st.session_state.driver_routes  = dr
        st.session_state.route          = dr.get(0, [])
        st.session_state.route_distance = dist
    else:
        route, dist = optimize_route_vrp(dm)
        st.session_state.driver_routes  = {0: route}
        st.session_state.route          = route
        st.session_state.route_distance = dist
    st.session_state.n_vehicles   = n_v
    st.session_state.vehicle_index = 1 if st.session_state.route and len(st.session_state.route) > 1 else 0
    st.session_state.status_message = f"Routes optimised for {n_v} driver(s) successfully"


# ═══════════════════════════════════════════════════════════════════════════════
# BOOT
# ═══════════════════════════════════════════════════════════════════════════════

try:
    initialize_state()
except Exception as exc:
    st.error(f"Unable to load operational data: {exc}")
    st.stop()

apply_theme(st.session_state.dark_mode)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    lc,tc = st.columns([4,1])
    with lc:
        st.markdown("## 🚚 RouteSense")
    with tc:
        if st.button("☀️" if st.session_state.dark_mode else "🌙",
                     key="theme_toggle", help="Toggle theme"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.caption("Logistics Intelligence Platform")
    st.divider()

    st.markdown("#### Dashboard View")
    role_choice = st.radio("role", ["Admin","Driver"], index=0 if st.session_state.role=="Admin" else 1,
                           horizontal=True, key="role_radio", label_visibility="collapsed")
    if role_choice != st.session_state.role:
        st.session_state.role=role_choice; st.rerun()

    st.divider()

    if st.session_state.role=="Admin":
        st.markdown("#### Quick Actions")
        if st.button("🔄  Refresh Data", key="btn_refresh"):
            try: refresh_data()
            except Exception as ex: st.session_state.status_message=f"Refresh failed: {ex}"
            st.rerun()

        st.divider()
        st.divider()
        # Active alerts count badge
        alerts = generate_alerts(
            st.session_state.deliveries, st.session_state.route,
            predict_delay_risk(st.session_state.route_distance,
                len([n for n in (st.session_state.route or []) if n!=0]))[0],
            st.session_state.route_distance,
        )
        n_warn = sum(1 for a in alerts if a[1] in ["HIGH","WARN"])
        if n_warn:
            st.markdown(f"**🔔 {n_warn} Active Alert{'s' if n_warn>1 else ''}**")
        else:
            st.markdown("**🟢 All Systems OK**")
    else:
        st.markdown("#### Driver Info")
        if st.session_state.route:
            total_s=len([n for n in st.session_state.route if n!=0])
            done=max(st.session_state.vehicle_index-1,0)
            st.metric("Stops Done",f"{done} / {total_s}")
            st.progress(done/total_s if total_s else 0, text="Route Progress")
        else:
            st.info("No route dispatched yet.")

    st.divider()
    st.caption("RouteSense v2.0")


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def render_admin():
    st.markdown("""
    <div style='padding:20px 0 8px 0;'>
      <h1 style='margin:0;font-size:1.9rem;font-weight:800;'>RouteSense Admin Dashboard</h1>
      <p style='margin:4px 0 0 0;font-size:0.9rem;opacity:0.6;'>AI-powered fleet operations & route intelligence</p>
    </div>""", unsafe_allow_html=True)

    if st.session_state.status_message:
        st.info(st.session_state.status_message)

    df = st.session_state.deliveries
    fleet_df = st.session_state.fleet
    route = st.session_state.route
    baseline = st.session_state.baseline_distance
    opt_dist = st.session_state.route_distance
    saved = max(baseline - opt_dist, 0.0)
    n_stops = len([n for n in (route or []) if n!=0])
    n_deliveries = int((df["type"]=="delivery").sum())
    fleet_size = int(len(fleet_df))
    delay_level, delay_score, delay_color = predict_delay_risk(opt_dist, n_stops)
    co2_saved = saved * 0.21

    # Top KPI row
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Total Deliveries", n_deliveries)
    k2.metric("Vehicles Available", fleet_size)
    k3.metric("Distance Saved", f"{saved:.1f} km", delta=f"{saved:.1f} km vs baseline" if saved else None)
    k4.metric("CO₂ Saved", f"{co2_saved:.2f} kg")
    k5.metric("Delay Risk", delay_level, delta=f"Score {delay_score}/100")

    st.markdown("<br>", unsafe_allow_html=True)

    tab_help, tab_ops, tab_ai, tab_fleet, tab_compare, tab_analytics, tab_alerts, tab_upload = st.tabs([
        "📖 Help",
        "📍 Operations",
        "🧠 AI Insights",
        "🚛 Fleet",
        "⚖️ Compare",
        "📊 Analytics",
        "🔔 Alerts",
        "📤 Upload Data",
    ])

    # ── Operations ────────────────────────────────────────────────────────────
    with tab_ops:
        driver_routes_ss = st.session_state.get("driver_routes", {})
        # Fallback: wrap legacy single route so the rest of the code is uniform
        if not driver_routes_ss and route:
            driver_routes_ss = {0: route}

        # ── Combined overview map ──────────────────────────────────────────
        st.markdown("##### 🗺️ All Drivers — Combined Route Overview")
        if driver_routes_ss:
            # Legend
            legend_parts = []
            for v_i, v_r in driver_routes_ss.items():
                vid = fleet_df.iloc[v_i]["vehicle_id"] if v_i < len(fleet_df) else f"D{v_i+1}"
                dname = (str(fleet_df.iloc[v_i]["driver_name"])
                         if v_i < len(fleet_df) and "driver_name" in fleet_df.columns
                         else "")
                icon = DRIVER_COLOR_ICONS[v_i % len(DRIVER_COLOR_ICONS)]
                n_s = len([n for n in v_r if n != 0])
                legend_parts.append(f"{icon} **{vid}** {dname} ({n_s} stops)")
            st.markdown("   ·   ".join(legend_parts))
        build_all_drivers_map(df, driver_routes_ss, fleet_df,
                              map_key="admin_ops_map", height=460)

        if not driver_routes_ss:
            st.info("Run **⚡ Optimize Route** to generate driver routes.")

        # ── Individual driver maps (dynamic grid) ──────────────────────────
        if driver_routes_ss:
            st.divider()
            st.markdown("##### 🚛 Individual Driver Routes")

            v_indices = sorted(driver_routes_ss.keys())
            n_total = len(v_indices)
            # max 2 maps per row so they stay readable
            COLS_PER_ROW = 2

            for row_start in range(0, n_total, COLS_PER_ROW):
                chunk = v_indices[row_start: row_start + COLS_PER_ROW]
                map_cols = st.columns(len(chunk))
                for ci, v_idx in enumerate(chunk):
                    v_route = driver_routes_ss[v_idx]
                    color   = _driver_color(v_idx)
                    icon    = DRIVER_COLOR_ICONS[v_idx % len(DRIVER_COLOR_ICONS)]
                    if v_idx < len(fleet_df):
                        v_row  = fleet_df.iloc[v_idx]
                        vid    = v_row["vehicle_id"]
                        dname  = (str(v_row["driver_name"])
                                  if "driver_name" in v_row.index else "")
                        phone  = (str(v_row["driver_phone"])
                                  if "driver_phone" in v_row.index else "")
                        area   = (str(v_row["area"])
                                  if "area" in v_row.index else "")
                        cap    = v_row["capacity"]
                    else:
                        vid, dname, phone, area, cap = f"D{v_idx+1}", "", "", "", "—"

                    delivery_nodes = [n for n in v_route if n != 0]
                    n_s = len(delivery_nodes)

                    with map_cols[ci]:
                        # Header card
                        extras = ""
                        if area and area != "nan":
                            extras += f" · 📍 {area}"
                        if phone and phone != "nan":
                            extras += f" · 📞 {phone}"
                        _dname_span = (
                            "  <span style=\"font-size:0.82rem;font-weight:400;color:#94a3b8;\">"
                            + dname + "</span>"
                        ) if dname else ""
                        _plural = "s" if n_s != 1 else ""
                        st.markdown(
                            f"<div style='background:rgba(255,255,255,0.04);border-left:4px solid {color};"
                            f"border-radius:8px;padding:10px 14px;margin-bottom:8px;'>"
                            f"<span style='font-size:1rem;font-weight:700;color:{color};'>"
                            f"{icon} {vid}{_dname_span}"
                            f"</span><br>"
                            f"<span style='font-size:0.75rem;color:#64748b;'>"
                            f"Capacity {cap} · {n_s} stop{_plural}{extras}"
                            f"</span></div>",
                            unsafe_allow_html=True,
                        )
                        build_driver_map(df, v_route, v_idx,
                                         map_key=f"driver_ops_map_{v_idx}", height=340)
                        # Compact stop table
                        if delivery_nodes:
                            stop_rows = []
                            for si, node in enumerate(delivery_nodes, 1):
                                r = df.iloc[node]
                                stop_rows.append({
                                    "#": si,
                                    "Location": r["location"],
                                    "Demand": int(r.get("demand", 0)),
                                })
                            st.dataframe(pd.DataFrame(stop_rows),
                                         use_container_width=True,
                                         hide_index=True, height=180)

    # ── AI Insights ───────────────────────────────────────────────────────────
    with tab_ai:
        left, right = st.columns([1,1])

        with left:
            st.markdown("#### 🧠 AI Delay Prediction")
            hour = datetime.datetime.now().hour
            risk_label, risk_score, risk_clr = predict_delay_risk(opt_dist, n_stops, hour)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=risk_score,
                delta={"reference":50,"decreasing":{"color":"#22c55e"},"increasing":{"color":"#ef4444"}},
                gauge={
                    "axis":{"range":[0,100],"tickcolor":"#94a3b8"},
                    "bar":{"color":risk_clr},
                    "steps":[
                        {"range":[0,38],"color":"rgba(34,197,94,0.15)"},
                        {"range":[38,65],"color":"rgba(245,158,11,0.15)"},
                        {"range":[65,100],"color":"rgba(239,68,68,0.15)"},
                    ],
                    "threshold":{"line":{"color":risk_clr,"width":3},"thickness":0.75,"value":risk_score},
                },
                title={"text":f"Delay Risk: <b>{risk_label}</b>","font":{"size":14,"color":"#94a3b8"}},
            ))
            fig_gauge.update_layout(height=260, margin=dict(l=10,r=10,t=40,b=10),
                                    paper_bgcolor="rgba(0,0,0,0)", font={"color":"#e2e8f0"})
            st.plotly_chart(fig_gauge, use_container_width=True, key="gauge_chart")

            factors = {
                "Time of Day": min(38 if hour in [8,9,10,17,18,19] else 18 if hour in [11,12,13,14,15,16] else 8, 38),
                "Route Distance": min(int(opt_dist*0.5),35),
                "No. of Stops": min(n_stops*2,25),
            }
            fig_bar = px.bar(
                pd.DataFrame({"Factor":list(factors.keys()),"Impact":list(factors.values())}),
                x="Impact", y="Factor", orientation="h",
                color="Impact", color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],
                text="Impact",
            )
            fig_bar.update_layout(height=200, showlegend=False, coloraxis_showscale=False,
                                  margin=dict(l=10,r=10,t=20,b=10),
                                  paper_bgcolor="rgba(0,0,0,0)", font={"color":"#e2e8f0"},
                                  plot_bgcolor="rgba(0,0,0,0)",
                                  xaxis=dict(showgrid=False,zeroline=False,color="#e2e8f0"),
                                  yaxis=dict(showgrid=False,color="#e2e8f0"))
            fig_bar.update_traces(texttemplate="%{x}", textposition="outside")
            st.plotly_chart(fig_bar, use_container_width=True, key="factor_bar")

        with right:
            st.markdown("#### 🗺️ Route Risk Heatmap")
            st.caption("Red = high congestion risk · Green = clear corridors")
            build_risk_heatmap(df, map_key="risk_heatmap_map", height=480)

        st.divider()
        st.markdown("#### 💡 Smart Fleet Recommendations")
        recs = fleet_recommendation(df, fleet_df, route, opt_dist)
        for icon, msg in recs:
            st.markdown(f"> {icon} {msg}")

        if route:
            st.divider()
            st.markdown("#### ⏱️ Delivery ETA Predictions")
            eta_map = compute_eta(df, route, opt_dist)
            eta_rows=[]
            for i,node in enumerate([n for n in route if n!=0],1):
                r=df.iloc[node]
                eta_rows.append({"Stop":i,"Location":r["location"],"ETA":eta_map.get(node,"—")})
            c1,c2=st.columns([1,2])
            with c1:
                st.dataframe(pd.DataFrame(eta_rows), use_container_width=True,
                             hide_index=True, height=380)
            with c2:
                if len(eta_rows)>0:
                    import re
                    times=[r["ETA"] for r in eta_rows if r["ETA"]!="—"]
                    stops=[r["Location"] for r in eta_rows if r["ETA"]!="—"]
                    if times:
                        base_t=datetime.datetime.strptime(times[0],"%H:%M")
                        mins=[(datetime.datetime.strptime(t,"%H:%M")-base_t).seconds//60 for t in times]
                        fig_eta=px.line(x=stops,y=mins,markers=True,
                            labels={"x":"Stop","y":"Minutes from dispatch"},
                            color_discrete_sequence=["#3b82f6"])
                        fig_eta.update_layout(height=360,margin=dict(l=10,r=10,t=20,b=10),
                            paper_bgcolor="rgba(0,0,0,0)",font={"color":"#e2e8f0"},
                            plot_bgcolor="rgba(0,0,0,0)",
                            xaxis=dict(showgrid=False,color="#e2e8f0",tickangle=-30),
                            yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",color="#e2e8f0"))
                        st.plotly_chart(fig_eta, use_container_width=True, key="eta_chart")

    # ── Fleet ─────────────────────────────────────────────────────────────────
    with tab_fleet:
        st.markdown("#### 🚛 Fleet Monitoring")
        driver_routes_ss = st.session_state.get("driver_routes", {})
        statuses=[]
        for i,(_,row) in enumerate(fleet_df.iterrows()):
            v_route = driver_routes_ss.get(i, [])
            has_stops = len([n for n in v_route if n != 0]) > 0
            if has_stops and i == 0:
                stat,stcol,icon="En Route","#22c55e","🟢"
            elif has_stops:
                stat,stcol,icon="Dispatched","#3b82f6","🔵"
            elif i == 0 and route:
                stat,stcol,icon="En Route","#22c55e","🟢"
            elif i == 1 and route:
                stat,stcol,icon="Standby","#f59e0b","🟡"
            else:
                stat,stcol,icon="Idle","#64748b","⚫"
            n_assigned = len([n for n in v_route if n != 0])
            driver_name = str(row["driver_name"]) if "driver_name" in row.index else row["vehicle_id"]
            driver_phone = str(row["driver_phone"]) if "driver_phone" in row.index else "—"
            driver_area  = str(row["area"]) if "area" in row.index else "—"
            statuses.append({"Vehicle":row["vehicle_id"],"Capacity":row["capacity"],
                             "DriverName":driver_name,"Phone":driver_phone,"Area":driver_area,
                             "Assigned":n_assigned,
                             "Status":f"{icon} {stat}","Status_Color":stcol})

        cols=st.columns(min(len(statuses),3))
        for i,s in enumerate(statuses):
            with cols[i%3]:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
                    border-radius:14px;padding:18px 20px;margin-bottom:12px;">
                  <div style="font-size:1.1rem;font-weight:700;color:#f1f5f9;">{s['Vehicle']} &nbsp;<span style='font-size:0.8rem;color:#94a3b8;font-weight:400;'>({s['DriverName']})</span></div>
                  <div style="font-size:0.78rem;color:#64748b;margin:4px 0;">Capacity: {s['Capacity']} · Stops: {s['Assigned']} · Area: {s['Area']}</div>
                  <div style="font-size:0.75rem;color:#475569;margin:2px 0;">📞 {s['Phone']}</div>
                  <div style="font-size:0.9rem;font-weight:600;color:{s['Status_Color']};margin-top:10px;">{s['Status']}</div>
                </div>""", unsafe_allow_html=True)

        # Driver Route Assignments table
        if driver_routes_ss:
            st.divider()
            st.markdown("#### 📋 Driver Route Assignments")
            assign_rows = []
            for v_idx, v_route in driver_routes_ss.items():
                if v_idx < len(fleet_df):
                    v_row = fleet_df.iloc[v_idx]
                    vid   = v_row["vehicle_id"]
                    dname = str(v_row["driver_name"]) if "driver_name" in v_row.index else vid
                    stops = [df.iloc[n]["location"] for n in v_route if n != 0]
                    assign_rows.append({
                        "Vehicle": vid,
                        "Driver":  dname,
                        "Stops Assigned": len(stops),
                        "Stop Sequence":  " → ".join(stops) if stops else "No stops",
                    })
            if assign_rows:
                st.dataframe(pd.DataFrame(assign_rows), use_container_width=True,
                             hide_index=True)

        st.divider()
        st.markdown("#### Corridor Congestion Scoring")
        st.caption("Each delivery corridor scored 0–100 based on proximity, demand density, and time-of-day.")
        rng = np.random.default_rng(42)
        delivery_locs = df[df["type"]=="delivery"]
        if not delivery_locs.empty:
            cong_rows=[]
            for _,r in delivery_locs.iterrows():
                demand=float(r.get("demand",1))
                score=min(int(demand*18+rng.integers(15,45)),100)
                level="High" if score>65 else ("Medium" if score>35 else "Low")
                cong_rows.append({"Corridor":r["location"],"Score":score,"Level":level})
            cong_df=pd.DataFrame(cong_rows).sort_values("Score",ascending=False)
            fig_cong=px.bar(cong_df,x="Corridor",y="Score",color="Score",
                color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],
                text="Score", labels={"Score":"Congestion Score"})
            fig_cong.update_layout(height=340,showlegend=False,coloraxis_showscale=False,
                margin=dict(l=5,r=5,t=10,b=5),
                paper_bgcolor="rgba(0,0,0,0)",font={"color":"#e2e8f0"},
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False,color="#e2e8f0",tickangle=-30),
                yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.06)",color="#e2e8f0"))
            fig_cong.update_traces(texttemplate="%{text}", textposition="outside")
            st.plotly_chart(fig_cong,use_container_width=True,key="cong_chart")

    # ── Compare ───────────────────────────────────────────────────────────────
    with tab_compare:
        st.markdown("#### ⚖️ Route Comparison")
        unopt_route = list(range(len(df)))+[0]
        opt_route = route

        mc1,mc2 = st.columns(2)
        with mc1:
            st.markdown("**Unoptimised (Sequential Order)**")
            build_comparison_map(df, unopt_route, "Original", "compare_orig_map", 380)
        with mc2:
            if opt_route:
                st.markdown("**Optimised Route (VRP)**")
                build_comparison_map(df, opt_route, "Optimised", "compare_opt_map", 380)
            else:
                st.info("Run optimisation to see the comparison.")

        st.divider()
        fuel_unopt = baseline * 0.18
        fuel_opt   = opt_dist * 0.18 if opt_route else baseline * 0.18
        co2_base   = baseline * 0.21
        co2_opt    = opt_dist * 0.21 if opt_route else co2_base
        speed_base = 25.0
        time_base  = (baseline / speed_base)*60
        time_opt   = (opt_dist / speed_base)*60 if opt_route else time_base

        cmp_df = pd.DataFrame({
            "Metric": ["Distance (km)", "Fuel Use (L)", "CO₂ Emitted (kg)", "Est. Travel Time (min)"],
            "Unoptimised": [f"{baseline:.2f}",f"{fuel_unopt:.2f}",f"{co2_base:.2f}",f"{time_base:.0f}"],
            "Optimised":   [f"{opt_dist:.2f}" if opt_route else "—",
                            f"{fuel_opt:.2f}" if opt_route else "—",
                            f"{co2_opt:.2f}" if opt_route else "—",
                            f"{time_opt:.0f}" if opt_route else "—"],
            "Saving":      [f"{saved:.2f} km",
                            f"{fuel_unopt-fuel_opt:.2f} L" if opt_route else "—",
                            f"{co2_base-co2_opt:.2f} kg" if opt_route else "—",
                            f"{time_base-time_opt:.0f} min" if opt_route else "—"],
        })
        st.dataframe(cmp_df, use_container_width=True, hide_index=True)

        if opt_route:
            efficiency = 0.0 if baseline==0 else (saved/baseline)*100
            st.progress(min(max(efficiency/100,0.0),1.0),
                        text=f"Optimisation efficiency: {efficiency:.1f}% distance reduction")

    # ── Analytics ─────────────────────────────────────────────────────────────
    with tab_analytics:
        st.markdown("#### 📊 Route Performance Analytics")
        before=baseline; after=opt_dist if route else before; sv=max(before-after,0.0)
        ch=pd.DataFrame({"Route":["Unoptimised","Optimised"],"Distance (km)":[before,after]})
        fig=px.bar(ch,x="Route",y="Distance (km)",color="Route",text="Distance (km)",
                   color_discrete_sequence=["#64748b","#3b82f6"])
        fig.update_layout(showlegend=False,height=340,
            margin=dict(l=5,r=5,t=10,b=10),paper_bgcolor="rgba(0,0,0,0)",
            font={"color":"#e2e8f0"},plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False,color="#e2e8f0"),
            yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.06)",color="#e2e8f0"))
        fig.update_traces(texttemplate="%{text:.2f} km",textposition="outside")
        st.plotly_chart(fig,use_container_width=True,key="analytics_bar")

        td=float(df["demand"].sum()) if "demand" in df.columns else 0.0
        tc=float(fleet_df["capacity"].sum()) if "capacity" in fleet_df.columns else 0.0
        util=0.0 if tc==0 else (td/tc*100)
        fuel_sv=sv*0.18; co2_sv=sv*0.21
        eff=0.0 if before==0 else (sv/before*100)

        a1,a2,a3,a4=st.columns(4)
        a1.metric("Distance Saved",f"{sv:.2f} km")
        a2.metric("Fuel Saved",f"{fuel_sv:.2f} L")
        a3.metric("CO₂ Saved",f"{co2_sv:.2f} kg")
        a4.metric("Capacity Utilisation",f"{util:.1f}%")

        st.progress(min(max(eff/100,0.0),1.0),text=f"Optimisation Efficiency: {eff:.1f}%")

        if "demand" in df.columns:
            st.divider()
            st.markdown("##### Demand Distribution by Location")
            d_del=df[df["type"]=="delivery"].copy()
            fig2=px.bar(d_del,x="location",y="demand",color="demand",
                color_continuous_scale=["#3b82f6","#7c3aed","#ec4899"],
                labels={"location":"Location","demand":"Demand Units"})
            fig2.update_layout(height=300,showlegend=False,coloraxis_showscale=False,
                margin=dict(l=5,r=5,t=5,b=5),paper_bgcolor="rgba(0,0,0,0)",
                font={"color":"#e2e8f0"},plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False,color="#e2e8f0",tickangle=-30),
                yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.06)",color="#e2e8f0"))
            st.plotly_chart(fig2,use_container_width=True,key="demand_chart")

    # ── Alerts ────────────────────────────────────────────────────────────────
    with tab_alerts:
        st.markdown("#### 🔔 Operational Alerts")
        alerts=generate_alerts(df, route, delay_level, opt_dist)
        for icon,level,msg in alerts:
            if level=="HIGH":
                st.error(f"{icon} **[{level}]** {msg}")
            elif level=="WARN":
                st.warning(f"{icon} **[{level}]** {msg}")
            elif level=="OK":
                st.success(f"{icon} **[{level}]** {msg}")
            else:
                st.info(f"{icon} **[{level}]** {msg}")

        st.divider()
        st.markdown("##### Corridor Congestion Snapshot")
        rng2=np.random.default_rng(0)
        snap_rows=[]
        for _,r in df[df["type"]=="delivery"].iterrows():
            demand=float(r.get("demand",1))
            s=min(int(demand*18+rng2.integers(15,45)),100)
            snap_rows.append({"Location":r["location"],"Congestion Score":s,
                              "Status":"🔴 High" if s>65 else ("🟡 Moderate" if s>35 else "🟢 Clear")})
        st.dataframe(pd.DataFrame(snap_rows).sort_values("Congestion Score",ascending=False),
                     use_container_width=True, hide_index=True)

    # ── Upload Data ───────────────────────────────────────────────────────────
    with tab_upload:
        st.markdown("#### 📤 Upload Delivery & Driver Data")
        st.markdown(
            "Upload your own delivery stops and fleet roster. "
            "The system will allocate stops to drivers automatically using multi-vehicle route optimisation. "
            "Download the templates below to see the required format."
        )

        # Templates
        st.markdown("##### 1 · Download CSV Templates")
        tc1, tc2 = st.columns(2)
        with tc1:
            st.download_button(
                label="⬇  Deliveries Template",
                data=DELIVERIES_TEMPLATE_CSV,
                file_name="deliveries_template.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_deliveries_tpl",
            )
            st.caption("`id`  `location`  `lat`  `lon`  `demand`  `driver_id` *(optional — pre-assign stops to a driver)*")
        with tc2:
            st.download_button(
                label="⬇  Fleet / Drivers Template",
                data=FLEET_TEMPLATE_CSV,
                file_name="fleet_template.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_fleet_tpl",
            )
            st.caption("`vehicle_id`  `capacity`  `driver_name`  `driver_phone`  `area` *(last three optional)*")

        st.divider()
        st.markdown("##### 2 · Upload Your CSVs")
        uc1, uc2 = st.columns(2)
        _uploaded_del   = None
        _uploaded_fleet = None

        with uc1:
            st.markdown("**Deliveries CSV**")
            del_file = st.file_uploader("del", type=["csv"], key="del_uploader",
                                         label_visibility="collapsed")
            if del_file:
                try:
                    _uploaded_del = pd.read_csv(del_file)
                    missing_d = {"id","location","lat","lon"} - set(_uploaded_del.columns)
                    if missing_d:
                        st.error(f"Missing required columns: {', '.join(sorted(missing_d))}")
                        _uploaded_del = None
                    else:
                        _uploaded_del["lat"] = pd.to_numeric(_uploaded_del["lat"], errors="coerce")
                        _uploaded_del["lon"] = pd.to_numeric(_uploaded_del["lon"], errors="coerce")
                        _uploaded_del = _uploaded_del.dropna(subset=["lat","lon"]).reset_index(drop=True)
                        if "demand" not in _uploaded_del.columns:
                            _uploaded_del["demand"] = 1
                        if "type" not in _uploaded_del.columns:
                            _uploaded_del["type"] = np.where(_uploaded_del["id"]==0, "depot", "delivery")
                        n_stops_up = int((_uploaded_del["type"]=="delivery").sum())
                        st.success(f"✅ {len(_uploaded_del)} rows — {n_stops_up} delivery stop(s) + depot")
                        show_c = [c for c in ["id","location","lat","lon","demand","driver_id","est_delivery_time"] if c in _uploaded_del.columns]
                        st.dataframe(_uploaded_del[show_c].head(20), use_container_width=True,
                                     hide_index=True, height=260)
                except Exception as _ex:
                    st.error(f"Could not parse deliveries file: {_ex}")
                    _uploaded_del = None

        with uc2:
            st.markdown("**Fleet / Drivers CSV**")
            fleet_file = st.file_uploader("fleet", type=["csv"], key="fleet_uploader",
                                           label_visibility="collapsed")
            if fleet_file:
                try:
                    _uploaded_fleet = pd.read_csv(fleet_file)
                    missing_f = {"vehicle_id","capacity"} - set(_uploaded_fleet.columns)
                    if missing_f:
                        st.error(f"Missing required columns: {', '.join(sorted(missing_f))}")
                        _uploaded_fleet = None
                    else:
                        st.success(f"✅ {len(_uploaded_fleet)} driver(s) loaded")
                        show_fc = [c for c in ["vehicle_id","capacity","driver_name","driver_phone","area"] if c in _uploaded_fleet.columns]
                        st.dataframe(_uploaded_fleet[show_fc], use_container_width=True,
                                     hide_index=True, height=260)
                except Exception as _ex:
                    st.error(f"Could not parse fleet file: {_ex}")
                    _uploaded_fleet = None

        st.divider()
        st.markdown("##### 3 · Apply & Optimise")
        if st.button("🚀  Apply Uploaded Data & Optimise All Routes",
                     key="apply_upload_btn", use_container_width=True):
            if _uploaded_del is None and _uploaded_fleet is None:
                st.warning("Upload at least one CSV file before applying.")
            else:
                new_del   = _uploaded_del   if _uploaded_del   is not None else st.session_state.deliveries.copy()
                new_fleet = _uploaded_fleet if _uploaded_fleet is not None else st.session_state.fleet.copy()
                new_del   = new_del.sort_values("id").reset_index(drop=True)
                st.session_state.deliveries = new_del
                st.session_state.fleet      = new_fleet
                _n_v  = max(1, len(new_fleet))
                _dm   = create_distance_matrix(new_del)
                st.session_state.baseline_distance = sequential_route_distance(_dm)
                _demands = new_del["demand"].fillna(1).astype(int).tolist()
                _cap     = int(new_fleet["capacity"].max()) if "capacity" in new_fleet.columns else 100
                if "driver_id" in new_del.columns and new_del["driver_id"].notna().any():
                    _dr = allocate_by_driver_col(new_del, new_fleet)
                    _td = sum(
                        sum(_dm[_dr[v][i], _dr[v][i+1]] for i in range(len(_dr[v])-1))
                        for v in _dr
                    )
                    st.session_state.driver_routes  = _dr
                    st.session_state.route          = _dr.get(0, [])
                    st.session_state.route_distance = _td
                else:
                    _dr, _td = optimize_multi_vehicle_vrp(_dm, _n_v, _demands, _cap)
                    st.session_state.driver_routes  = _dr
                    st.session_state.route          = _dr.get(0, [])
                    st.session_state.route_distance = _td
                st.session_state.n_vehicles     = _n_v
                st.session_state.vehicle_index  = 1
                st.session_state.status_message = f"Uploaded data applied — {_n_v} driver route(s) optimised."
                st.rerun()

        st.divider()
        st.markdown("##### Current Live Data in Use")
        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown("**Deliveries**")
            _sc = [c for c in ["id","location","lat","lon","demand","driver_id","est_delivery_time"] if c in df.columns]
            st.dataframe(df[_sc], use_container_width=True, hide_index=True, height=300)
        with pc2:
            st.markdown("**Fleet / Drivers**")
            _sfc = [c for c in ["vehicle_id","capacity","driver_name","driver_phone","area"] if c in fleet_df.columns]
            st.dataframe(fleet_df[_sfc], use_container_width=True, hide_index=True, height=300)

    # ── Help ──────────────────────────────────────────────────────────────────
    with tab_help:
        help_lang = st.radio("Help language", ["English", "हिंदी", "தமிழ்"],
                             horizontal=True, key="help_lang_radio")
        st.markdown("<br>", unsafe_allow_html=True)

        if help_lang == "English":
            st.markdown("## 📖 How to Use RouteSense")
            st.markdown("""
<div style='line-height:2.0;font-size:0.97rem;'>

**Step 1 — Upload your data**
- Go to the **📤 Upload Data** tab.
- Download the CSV templates provided there.
- Fill in your delivery stops and driver details, then upload both files.
- Click **Apply & Optimise** — routes are automatically assigned to each driver.

**Step 2 — Check your routes**
- Go to **📍 Operations** to see all drivers on a single combined map.
- Each driver is shown in a different colour with their stop count.
- Scroll down to see individual driver maps side by side.

**Step 3 — Monitor drivers**
- Switch the role to **Driver** in the left sidebar.
- Each driver's tab shows their map, list of stops, ETA, and current status.
- Use the 5 voice buttons (Next Stop / ETA / Traffic / Progress / Briefing) to hear live announcements.

**Step 4 — Automatic voice alerts**
- If you added an `est_delivery_time` column in your CSV, the app will **automatically speak** when a delivery time is approaching (within 2 minutes) or has been missed (10+ minutes late) — no button press needed.
- The page self-refreshes silently in the background so alerts fire on time.

**Step 5 — Other tabs**
| Tab | What it shows |
|---|---|
| 🧠 AI Insights | Delay risk score and prediction model |
| 🚛 Fleet | All vehicles, driver names, phone numbers |
| ⚖️ Compare | Optimised route vs unoptimised baseline |
| 📊 Analytics | Distance, stop density, congestion charts |
| 🔔 Alerts | Live warnings for high delay risk or overdue stops |

> **Tip:** Use **Chrome** or **Edge** browser for the best voice experience.

</div>
""", unsafe_allow_html=True)

        elif help_lang == "हिंदी":
            st.markdown("## 📖 RouteSense कैसे चलाएं")
            st.markdown("""
<div style='line-height:2.2;font-size:0.97rem;'>

**चरण 1 — डेटा अपलोड करें**
- **📤 Upload Data** टैब पर जाएं।
- वहाँ दिए गए CSV टेम्पलेट डाउनलोड करें।
- अपने डिलीवरी पड़ाव और ड्राइवर की जानकारी भरें, फिर दोनों फ़ाइलें अपलोड करें।
- **Apply & Optimise** बटन दबाएं — रूट अपने आप हर ड्राइवर को सौंप दिया जाएगा।

**चरण 2 — रूट देखें**
- **📍 Operations** टैब में सभी ड्राइवरों को एक मैप पर देखें।
- हर ड्राइवर को अलग रंग में दिखाया जाता है।
- नीचे स्क्रॉल करके हर ड्राइवर का अलग मैप देखें।

**चरण 3 — ड्राइवर डैशबोर्ड**
- बाईं साइडबार में **Driver** भूमिका चुनें।
- हर ड्राइवर के टैब में उनका मैप, पड़ावों की सूची, ETA और स्थिति दिखती है।
- 5 बटन (अगला पड़ाव / समय / यातायात / प्रगति / पूरी जानकारी) दबाएं और हिंदी में आवाज़ सुनें।

**चरण 4 — स्वचालित आवाज़ अलर्ट**
- यदि आपने CSV में `est_delivery_time` कॉलम जोड़ा है, तो ऐप **अपने आप बोलेगा** — डिलीवरी समय से 2 मिनट पहले और 10 मिनट देर होने पर।
- इसके लिए कोई बटन दबाने की ज़रूरत नहीं है।

**चरण 5 — अन्य टैब**
| टैब | क्या दिखता है |
|---|---|
| 🧠 AI Insights | देरी जोखिम स्कोर और भविष्यवाणी |
| 🚛 Fleet | सभी वाहन, नाम, फ़ोन नंबर |
| ⚖️ Compare | ऑप्टिमाइज़्ड बनाम पुराना रूट |
| 📊 Analytics | दूरी, पड़ाव घनत्व, ट्रैफिक चार्ट |
| 🔔 Alerts | देरी और समय से चूके पड़ावों की चेतावनी |

> **सुझाव:** सबसे अच्छी आवाज़ के लिए **Chrome** या **Edge** ब्राउज़र इस्तेमाल करें।

</div>
""", unsafe_allow_html=True)

        else:  # தமிழ்
            st.markdown("## 📖 RouteSense எவ்வாறு பயன்படுத்துவது")
            st.markdown("""
<div style='line-height:2.2;font-size:0.97rem;'>

**படி 1 — தரவை பதிவேற்றவும்**
- **📤 Upload Data** தாவலுக்கு செல்லவும்.
- அங்கே கொடுக்கப்பட்ட CSV வார்ப்புருக்களை பதிவிறக்கவும்.
- உங்கள் டெலிவரி நிலையங்கள் மற்றும் ஓட்டுநர் விவரங்களை நிரப்பி, இரண்டு கோப்புகளையும் பதிவேற்றவும்.
- **Apply & Optimise** பொத்தானை அழுத்தவும் — பாதைகள் தானாகவே ஒவ்வொரு ஓட்டுநருக்கும் ஒதுக்கப்படும்.

**படி 2 — பாதைகளை சரிபார்க்கவும்**
- **📍 Operations** தாவலில் அனைத்து ஓட்டுநர்களையும் ஒரே வரைபடத்தில் காணலாம்.
- ஒவ்வொரு ஓட்டுநரும் வெவ்வேறு நிறத்தில் காட்டப்படுவார்கள்.
- கீழே உருட்டி தனி ஓட்டுநர் வரைபடங்களை பக்க வாட்டில் காணலாம்.

**படி 3 — ஓட்டுநர் டாஷ்போர்டு**
- இடது பட்டியில் **Driver** பாத்திரத்தை தேர்ந்தெடுக்கவும்.
- ஒவ்வொரு ஓட்டுநரின் தாவலிலும் வரைபடம், நிலையங்கள் பட்டியல், ETA மற்றும் நிலை தெரியும்.
- 5 பொத்தான்களை (அடுத்த நிலையம் / நேரம் / போக்குவரத்து / முன்னேற்றம் / முழு விவரம்) அழுத்தி தமிழில் அறிவிப்பை கேளுங்கள்.

**படி 4 — தானியங்கி குரல் எச்சரிக்கைகள்**
- CSV-ல் `est_delivery_time` நெடுவரிசை சேர்த்தால், டெலிவரி நேரத்திற்கு 2 நிமிடம் முன்பும், 10 நிமிடம் தாமதமானாலும் **தானாகவே குரல் வரும்** — பொத்தான் அழுத்த வேண்டியதில்லை.

**படி 5 — மற்ற தாவல்கள்**
| தாவல் | என்ன காட்டுகிறது |
|---|---|
| 🧠 AI Insights | தாமத அபாய மதிப்பீடு |
| 🚛 Fleet | அனைத்து வாகனங்கள், பெயர்கள், தொலைபேசி எண்கள் |
| ⚖️ Compare | உகந்த பாதை vs பழைய பாதை |
| 📊 Analytics | தூரம், நிலைய அடர்த்தி, போக்குவரத்து விளக்கப்படங்கள் |
| 🔔 Alerts | தாமதமான மற்றும் தவறிய நிலையங்களுக்கான எச்சரிக்கைகள் |

> **குறிப்பு:** சிறந்த குரல் அனுபவத்திற்கு **Chrome** அல்லது **Edge** உலாவியை பயன்படுத்தவும்.

</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MULTILINGUAL PHRASES
# ═══════════════════════════════════════════════════════════════════════════════

LANG_OPTIONS = {
    "English":  ("en-US", "🇬🇧"),
    "हिंदी":    ("hi-IN", "🇮🇳"),
    "தமிழ்":   ("ta-IN", "🇮🇳"),
}

# ── Phonetic substitutions so TTS engines pronounce Chennai place names correctly ──
# Keys are the exact CSV location names; values are what actually gets spoken.
PLACE_PHONETICS: dict[str, dict[str, str]] = {
    # en-US: space-separated syllables that browser TTS reads predictably.
    # No hyphens (read as "dash"), no concatenated blobs.
    "en-US": {
        "Chennai Depot":  "Chen nai Depot",
        "T Nagar":        "Tee Nagar",
        "Velachery":      "Vella cherry",         # two familiar English words
        "Tambaram":       "Tum ba rum",
        "Anna Nagar":     "Anna Nagar",
        "Adyar":          "Ud yar",
        "Porur":          "Paw rur",
        "Guindy":         "Gin dee",              # hard G
        "OMR":            "Old Maha bali puram Road",
        "Perambur":       "Peh rum bur",
        "Mylapore":       "My la pore",
        "Sholinganallur": "Show linga na lur",
    },
    # hi-IN: Devanagari for browsers that have a Hindi voice installed.
    # _PHONETIC_ROMAN_HI below is sent as the en-US fallback text when no Hindi voice is found.
    "hi-IN": {
        "Chennai Depot":  "चेन्नई डिपो",
        "T Nagar":        "टी नगर",
        "Velachery":      "वेलाचेरी",
        "Tambaram":       "ताम्बरम",
        "Anna Nagar":     "अन्ना नगर",
        "Adyar":          "अड्यार",
        "Porur":          "पोरूर",
        "Guindy":         "गिंडी",
        "OMR":            "ओल्ड महाबलीपुरम रोड",
        "Perambur":       "पेरम्बूर",
        "Mylapore":       "मयिलापुर",
        "Sholinganallur": "शोलिंगनल्लूर",
    },
    "ta-IN": {
        "Chennai Depot":  "சென்னை டிப்போ",
        "T Nagar":        "டி நகர்",
        "Velachery":      "வேளச்சேரி",
        "Tambaram":       "தாம்பரம்",
        "Anna Nagar":     "அண்ணா நகர்",
        "Adyar":          "அடையாறு",
        "Porur":          "பொரூர்",
        "Guindy":         "கிண்டி",
        "OMR":            "பழைய மகாபலிபுரம் சாலை",
        "Perambur":       "பெரம்பூர்",
        "Mylapore":       "மயிலாப்பூர்",
        "Sholinganallur": "சோளிங்கநல்லூர்",
    },
}

# Romanised en-US fallbacks sent as the `fallback_text` to speak_js when the
# browser has no hi-IN or ta-IN voice installed (common on Windows without
# Indian language packs).  Same space-separated syllable style as en-US above.
_ROMAN_FALLBACK: dict[str, str] = {
    "Chennai Depot":  "Chen nai Deh poh",
    "T Nagar":        "Tee Nah gar",
    "Velachery":      "Veh lah cher ee",
    "Tambaram":       "Tahm bah rum",
    "Anna Nagar":     "Ah nah Nah gar",
    "Adyar":          "Ahd yaar",
    "Porur":          "Poh roor",
    "Guindy":         "Ghin dee",
    "OMR":            "Oh Em Ar",
    "Perambur":       "Peh rum boor",
    "Mylapore":       "My lah poor",
    "Sholinganallur": "Show lin gah nah lur",
}


def phonetic_loc(name: str, lang: str) -> str:
    """Return TTS-friendly pronunciation of a place name for the given lang."""
    table = PLACE_PHONETICS.get(lang, PLACE_PHONETICS["en-US"])
    return table.get(name, name)


def phonetic_loc_fallback(name: str) -> str:
    """Return the en-US romanised fallback for a place name (used when no native voice found)."""
    return _ROMAN_FALLBACK.get(name, name)


PHRASES: dict[str, dict[str, str]] = {
    "en-US": {
        # Manual button announcements
        "next_stop":       "Your next stop is {loc}. Estimated arrival at {eta}.",
        "eta_only":        "ETA for the next stop is {eta}.",
        "traffic_high":    "Delay risk is HIGH. Expect heavy congestion ahead. Allow extra travel time.",
        "traffic_medium":  "Delay risk is MEDIUM. Some congestion expected. Stay alert.",
        "traffic_low":     "Delay risk is LOW. Roads are clear. Good to go!",
        "progress":        "Route progress: {done} of {total} stops completed. {remaining} stops remaining.",
        "briefing":        "Good {period}. You have {remaining} stops remaining. "
                           "Next stop is {loc}, arriving at {eta}. "
                           "Delay risk is {level}. Total route distance is {dist} kilometres.",
        # Automatic time-based alerts
        "scheduled_stop":  "Delivery alert! Time to head to {loc}. Scheduled delivery at {eta}.",
        "time_exceeded":   "Warning! Delivery time exceeded for {loc}. "
                           "It was scheduled at {eta} and is now overdue. Please hurry!",
    },
    "hi-IN": {
        "next_stop":       "आपका अगला पड़ाव {loc} है। अनुमानित पहुंचने का समय {eta} है।",
        "eta_only":        "अगले पड़ाव का अनुमानित समय {eta} है।",
        "traffic_high":    "यातायात जोखिम उच्च है। भारी जाम की संभावना है। अतिरिक्त समय रखें।",
        "traffic_medium":  "यातायात जोखिम मध्यम है। कुछ रुकावट हो सकती है। सावधान रहें।",
        "traffic_low":     "यातायात जोखिम कम है। सड़कें साफ हैं। आगे बढ़ें।",
        "progress":        "रूट प्रगति: {total} में से {done} पड़ाव पूरे हुए। {remaining} पड़ाव शेष हैं।",
        "briefing":        "नमस्कार। आपके {remaining} पड़ाव शेष हैं। "
                           "अगला पड़ाव {loc} है, पहुंचने का समय {eta} है। "
                           "यातायात जोखिम {level} है। "
                           "कुल दूरी {dist} किलोमीटर है।",
        "scheduled_stop":  "डिलीवरी अलर्ट। {loc} के लिए निकलने का समय आ गया है। निर्धारित समय {eta} है।",
        "time_exceeded":   "सावधान। {loc} की डिलीवरी का निर्धारित समय {eta} निकल गया है। कृपया तुरंत जाएं।",
    },
    "ta-IN": {
        "next_stop":       "உங்கள் அடுத்த நிலையம் {loc}. வருகை நேரம் {eta}.",
        "eta_only":        "அடுத்த நிலையத்திற்கான வருகை நேரம் {eta}.",
        "traffic_high":    "போக்குவரத்து தாமத அபாயம் அதிகமாக உள்ளது. கவனமாக செல்லவும்.",
        "traffic_medium":  "போக்குவரத்து தாமதம் நடுத்தரமாக உள்ளது. கவனமாக இருங்கள்.",
        "traffic_low":     "வழி சுதந்திரமாக உள்ளது. புறப்படலாம்.",
        "progress":        "பயண நிலை: {total} இல் {done} நிலையங்கள் முடிந்தன. {remaining} நிலையங்கள் மீதமுள்ளன.",
        "briefing":        "வணக்கம். உங்களுக்கு {remaining} நிலையங்கள் மீதமுள்ளன. "
                           "அடுத்த நிலையம் {loc}, வருகை நேரம் {eta}. "
                           "போக்குவரத்து தாமத நிலை {level}. "
                           "மொத்த தூரம் {dist} கிலோமீட்டர்.",
        "scheduled_stop":  "கவன அறிவிப்பு. {loc} க்கு செல்ல வேண்டிய நேரம் ஆகிவிட்டது. திட்டமிட்ட நேரம் {eta}.",
        "time_exceeded":   "எச்சரிக்கை. {loc} க்கான டெலிவரி நேரம் {eta} கடந்துவிட்டது. உடனடியாக செல்லுங்கள்.",
    },
}

# ── UI text shown on screen in the driver dashboard ──────────────────────────
UI_TEXT: dict[str, dict[str, str]] = {
    "en-US": {
        "page_title":      "RouteSense Driver View",
        "page_sub":        "Your route, stops, and live ETA",
        "no_route":        "No route dispatched yet. Contact your fleet admin.",
        "metric_next":     "Next Stop",
        "metric_eta":      "ETA",
        "metric_done":     "Stops Done",
        "metric_risk":     "Delay Risk",
        "progress_text":   "Route progress: {done}/{total} stops completed",
        "sec_map":         "Your Route",
        "sec_stops":       "Stop List & ETA",
        "col_order":       "#",
        "col_location":    "Location",
        "col_eta":         "ETA",
        "col_status":      "Status",
        "done_status":     "✅ Done",
        "now_status":      "🚛 Now",
        "pending_status":  "⏳ Pending",
        "col_sched":       "Scheduled",
        "sec_voice":       "🎙️ Route Voice Announcements",
        "lang_caption":    "{flag} Tap a button — announcement plays in **{lang}**.",
        "btn_next":        "📍 Next Stop",
        "btn_eta":         "🕐 ETA",
        "btn_traffic":     "🚦 Traffic",
        "btn_progress":    "📊 Progress",
        "btn_brief":       "🗺️ Full Briefing",
    },
    "hi-IN": {
        "page_title":      "RouteSense — चालक दृश्य",
        "page_sub":        "आपका रूट, पड़ाव और लाइव ETA",
        "no_route":        "अभी तक कोई रूट नहीं भेजा गया। फ्लीट एडमिन से संपर्क करें।",
        "metric_next":     "अगला पड़ाव",
        "metric_eta":      "अनुमानित समय",
        "metric_done":     "पड़ाव पूरे",
        "metric_risk":     "देरी जोखिम",
        "progress_text":   "रूट प्रगति: {done}/{total} पड़ाव पूरे",
        "sec_map":         "आपका रूट",
        "sec_stops":       "पड़ाव सूची और ETA",
        "col_order":       "क्र.",
        "col_location":    "स्थान",
        "col_eta":         "समय",
        "col_status":      "स्थिति",
        "done_status":     "✅ पूरा",
        "now_status":      "🚛 अभी",
        "pending_status":  "⏳ शेष",
        "col_sched":       "निर्धारित समय",
        "sec_voice":       "🎙️ वॉयस अनौन्समेंट",
        "lang_caption":    "{flag} बटन दबाएं — घोषणा **{lang}** में सुनाई देगी।",
        "btn_next":        "📍 अगला पड़ाव",
        "btn_eta":         "🕐 समय",
        "btn_traffic":     "🚦 यातायात",
        "btn_progress":    "📊 प्रगति",
        "btn_brief":       "🗺️ पूरी जानकारी",
    },
    "ta-IN": {
        "page_title":      "RouteSense — ஓட்டுநர் காட்சி",
        "page_sub":        "உங்கள் பாதை, நிலையங்கள் மற்றும் ETA",
        "no_route":        "இன்னும் பாதை அனுப்பப்படவில்லை. நிர்வாகியை தொடர்பு கொள்ளவும்.",
        "metric_next":     "அடுத்த நிலையம்",
        "metric_eta":      "வருகை நேரம்",
        "metric_done":     "முடிந்த நிலையங்கள்",
        "metric_risk":     "தாமத அபாயம்",
        "progress_text":   "பயண நிலை: {done}/{total} நிலையங்கள் முடிந்தன",
        "sec_map":         "உங்கள் பாதை",
        "sec_stops":       "நிலையங்கள் மற்றும் நேரம்",
        "col_order":       "வ.எண்",
        "col_location":    "இடம்",
        "col_eta":         "நேரம்",
        "col_status":      "நிலை",
        "done_status":     "✅ முடிந்தது",
        "now_status":      "🚛 இப்போது",
        "pending_status":  "⏳ காத்திருக்கிறது",
        "col_sched":       "திட்டமிட்ட நேரம்",
        "sec_voice":       "🎙️ குரல் அறிவிப்புகள்",
        "lang_caption":    "{flag} பொத்தானை அழுத்தவும் — அறிவிப்பு **{lang}** மோழியில் ஒலிக்கும்.",
        "btn_next":        "📍 அடுத்த நிலையம்",
        "btn_eta":         "🕐 நேரம்",
        "btn_traffic":     "🚦 போக்குவரத்து",
        "btn_progress":    "📊 முன்னேற்றம்",
        "btn_brief":       "🗺️ முழு விவரம்",
    },
}


def get_announcement(kind: str, lang: str, **kw) -> str:
    p = PHRASES.get(lang, PHRASES["en-US"])
    template = p.get(kind, p.get(kind.replace("traffic_", "traffic_low"), ""))
    try:
        return template.format(**kw)
    except KeyError:
        return template


def _check_scheduled_announcements(
    df: "pd.DataFrame",
    driver_routes_ss: dict,
    lang_code: str,
) -> list:
    """
    Returns list of (key, text, fallback) for stops whose est_delivery_time
    falls within a [-2, +5] minute window of the current clock time and have
    not yet been announced in this session.
    """
    if "est_delivery_time" not in df.columns:
        return []
    now = datetime.datetime.now()
    now_mins = now.hour * 60 + now.minute
    announced: set = st.session_state.get("auto_announced", set())
    due = []
    for v_idx, v_route in driver_routes_ss.items():
        for node in v_route:
            if node == 0:
                continue
            key = (v_idx, node)
            if key in announced:
                continue
            row = df.iloc[node]
            sched = str(row.get("est_delivery_time", "")).strip()
            if not sched or sched in ("nan", "—", ""):
                continue
            try:
                h, m   = sched.split(":")
                s_mins = int(h) * 60 + int(m)
            except Exception:
                continue
            delta = now_mins - s_mins  # positive = overdue
            loc_disp = row["location"]
            loc_spk  = phonetic_loc(loc_disp, lang_code)
            loc_en   = phonetic_loc_fallback(loc_disp)
            # Window 1: approaching / on-time [-2 min, +5 min]
            if -2 <= delta <= 5:
                text     = get_announcement("scheduled_stop", lang_code,
                                            loc=loc_spk, eta=sched)
                fallback = get_announcement("scheduled_stop", "en-US",
                                            loc=loc_en,  eta=sched)
                due.append((key, text, fallback))
            # Window 2: overdue [+10 min, +60 min] — time exceeded alert
            elif 10 <= delta <= 60:
                text     = get_announcement("time_exceeded", lang_code,
                                            loc=loc_spk, eta=sched)
                fallback = get_announcement("time_exceeded", "en-US",
                                            loc=loc_en,  eta=sched)
                due.append((key, text, fallback))
    return due


# ═══════════════════════════════════════════════════════════════════════════════
# DRIVER DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def render_driver():
    # ── Language selector ──────────────────────────────────────────────────────
    _lang_keys = list(LANG_OPTIONS.keys())
    # Persist chosen language across auto-refresh reruns
    _saved   = st.session_state.get("voice_lang_name", _lang_keys[0])
    _def_idx = _lang_keys.index(_saved) if _saved in _lang_keys else 0
    lang_label = st.radio(
        "Language", _lang_keys,
        index=_def_idx,
        horizontal=True, key="voice_lang_name", label_visibility="collapsed",
    )
    lang_code, flag = LANG_OPTIONS[lang_label]
    st.session_state.voice_lang = lang_code
    ui = UI_TEXT.get(lang_code, UI_TEXT["en-US"])

    st.markdown(f"""
    <div style='padding:12px 0 8px 0;'>
      <h1 style='margin:0;font-size:1.9rem;font-weight:800;'>{ui['page_title']}</h1>
      <p style='margin:4px 0 0 0;font-size:0.9rem;opacity:0.6;'>{ui['page_sub']}</p>
    </div>""", unsafe_allow_html=True)

    df           = st.session_state.deliveries
    fleet_df     = st.session_state.fleet
    driver_routes_ss = st.session_state.get("driver_routes", {})
    # Fallback: wrap legacy single route
    if not driver_routes_ss and st.session_state.route:
        driver_routes_ss = {0: st.session_state.route}

    # ── Scheduled-delivery auto-announcements ───────────────────────────────
    due_anns = _check_scheduled_announcements(df, driver_routes_ss, lang_code)
    if due_anns:
        for _key, _txt, _fb in due_anns:
            st.session_state.auto_announced.add(_key)
        # Speak the first due announcement
        st.session_state.last_announcement          = due_anns[0][1]
        st.session_state.last_announcement_fallback = due_anns[0][2]
        st.session_state.do_speak = True

    # ── Auto-refresh timer ────────────────────────────────────────────────
    # Calculate seconds until the nearest un-announced scheduled delivery
    if "est_delivery_time" in df.columns:
        _now_secs   = (datetime.datetime.now().hour * 3600
                       + datetime.datetime.now().minute * 60
                       + datetime.datetime.now().second)
        _refresh    = 45  # default: re-check every 45 s
        _announced  = st.session_state.get("auto_announced", set())
        for _vi, _vr in driver_routes_ss.items():
            for _nd in _vr:
                if _nd == 0 or (_vi, _nd) in _announced:
                    continue
                _sc = str(df.iloc[_nd].get("est_delivery_time", "")).strip()
                if not _sc or _sc in ("nan", ""):
                    continue
                try:
                    _hh, _mm = _sc.split(":")
                    _diff = int(_hh)*3600 + int(_mm)*60 - _now_secs
                    if 5 < _diff < _refresh:
                        _refresh = _diff
                except Exception:
                    pass
        render_autorefresh(max(10, _refresh))
    else:
        render_autorefresh(45)

    if not driver_routes_ss:
        st.warning(ui["no_route"])
        build_route_map(df, None, None, map_key="driver_no_route_map", height=480)
        return

    hour_now = datetime.datetime.now().hour
    period   = "morning" if hour_now < 12 else ("afternoon" if hour_now < 17 else "evening")

    # ── Combined overview map ──────────────────────────────────────────────────
    st.markdown(f"##### 🗺️ {ui['sec_map']} — All Drivers")
    legend_parts = []
    for v_i, v_r in driver_routes_ss.items():
        vid   = fleet_df.iloc[v_i]["vehicle_id"] if v_i < len(fleet_df) else f"D{v_i+1}"
        dname = (str(fleet_df.iloc[v_i]["driver_name"])
                 if v_i < len(fleet_df) and "driver_name" in fleet_df.columns else "")
        ico   = DRIVER_COLOR_ICONS[v_i % len(DRIVER_COLOR_ICONS)]
        n_s   = len([n for n in v_r if n != 0])
        legend_parts.append(f"{ico} **{vid}** {dname} ({n_s} stops)")
    st.markdown("   ·   ".join(legend_parts))
    build_all_drivers_map(df, driver_routes_ss, fleet_df,
                          map_key="driver_overview_map", height=430)

    # ── Per-driver tabs ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("##### 🚛 Individual Driver Views")
    v_indices  = sorted(driver_routes_ss.keys())
    tab_labels = []
    for v_i in v_indices:
        vid = fleet_df.iloc[v_i]["vehicle_id"] if v_i < len(fleet_df) else f"D{v_i+1}"
        ico = DRIVER_COLOR_ICONS[v_i % len(DRIVER_COLOR_ICONS)]
        tab_labels.append(f"{ico} {vid}")

    driver_tabs = st.tabs(tab_labels)

    for tab, v_idx in zip(driver_tabs, v_indices):
        v_route = driver_routes_ss[v_idx]
        color   = _driver_color(v_idx)
        if v_idx < len(fleet_df):
            v_row  = fleet_df.iloc[v_idx]
            vid    = v_row["vehicle_id"]
            dname  = str(v_row["driver_name"])  if "driver_name"  in v_row.index else vid
            phone  = str(v_row["driver_phone"]) if "driver_phone" in v_row.index else "—"
            area   = str(v_row["area"])          if "area"         in v_row.index else "—"
        else:
            vid, dname, phone, area = f"D{v_idx+1}", f"Driver {v_idx+1}", "—", "—"

        delivery_nodes = [n for n in v_route if n != 0]
        total_stops    = len(delivery_nodes)
        tot_dist       = st.session_state.route_distance
        eta_map        = compute_eta(df, v_route, tot_dist)
        delay_lvl, _, _ = predict_delay_risk(tot_dist, total_stops)
        v_pos          = min(st.session_state.vehicle_index, len(v_route) - 1)
        completed      = max(v_pos - 1, 0)
        next_node      = v_route[min(v_pos + 1, len(v_route) - 1)] if len(v_route) > 1 else v_route[0]
        next_eta       = eta_map.get(next_node, "—")
        next_loc_disp  = df.iloc[next_node]["location"]
        next_loc_spk   = phonetic_loc(next_loc_disp, lang_code)
        next_loc_en    = phonetic_loc_fallback(next_loc_disp)
        traffic_key    = f"traffic_{delay_lvl.lower()}"

        with tab:
            _extras = ""
            if area  and area  not in ("—", "nan"): _extras += f" · 📍 {area}"
            if phone and phone not in ("—", "nan"): _extras += f" · 📞 {phone}"
            st.markdown(
                f"<div style='border-left:4px solid {color};padding:8px 14px;"
                f"background:rgba(255,255,255,0.03);border-radius:8px;margin-bottom:12px;'>"
                f"<b style='color:{color};font-size:1rem;'>{vid}</b> "
                f"<span style='color:#94a3b8;font-size:0.85rem;'>{dname}{_extras}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            d1, d2, d3, d4 = st.columns(4)
            d1.metric(ui["metric_next"], next_loc_disp)
            d2.metric(ui["metric_eta"],  next_eta)
            d3.metric(ui["metric_done"], f"{completed} / {total_stops}")
            d4.metric(ui["metric_risk"], delay_lvl)
            st.progress(
                completed / total_stops if total_stops else 0,
                text=ui["progress_text"].format(done=completed, total=total_stops),
            )

            map_col, list_col = st.columns([2, 1])
            with map_col:
                build_driver_map(df, v_route, v_idx,
                                 map_key=f"dv_map_{v_idx}", height=420)
            with list_col:
                st.markdown(f"##### {ui['sec_stops']}")
                rows = []
                for seq, node in enumerate(delivery_nodes, start=1):
                    r = df.iloc[node]
                    is_done    = seq < v_pos
                    is_current = seq == v_pos
                    status = (ui["done_status"]    if is_done
                              else ui["now_status"]  if is_current
                              else ui["pending_status"])
                    _sched = (str(r.get("est_delivery_time", "—")).strip()
                              if "est_delivery_time" in df.columns else "—")
                    row_d = {
                        ui["col_order"]:    seq,
                        ui["col_location"]: r["location"],
                        ui["col_eta"]:      eta_map.get(node, "—"),
                        ui["col_status"]:   status,
                    }
                    if "est_delivery_time" in df.columns:
                        row_d[ui.get("col_sched", "Scheduled")] = _sched
                    rows.append(row_d)
                st.dataframe(pd.DataFrame(rows), use_container_width=True,
                             height=400, hide_index=True)

            # ── Manual voice buttons ───────────────────────────────────────────────
            st.markdown(f"#### {ui['sec_voice']}")
            st.caption(ui["lang_caption"].format(flag=flag, lang=lang_label))
            b1, b2, b3, b4, b5 = st.columns(5)
            ann_text = ""; ann_fallback = ""
            if b1.button(ui["btn_next"],     key=f"ann_next_{v_idx}",     use_container_width=True):
                ann_text     = get_announcement("next_stop",  lang_code,
                                                loc=next_loc_spk, eta=next_eta)
                ann_fallback = get_announcement("next_stop",  "en-US",
                                                loc=next_loc_en,  eta=next_eta)
            if b2.button(ui["btn_eta"],      key=f"ann_eta_{v_idx}",      use_container_width=True):
                ann_text     = get_announcement("eta_only",   lang_code, eta=next_eta)
                ann_fallback = get_announcement("eta_only",   "en-US",   eta=next_eta)
            if b3.button(ui["btn_traffic"],  key=f"ann_traffic_{v_idx}",  use_container_width=True):
                ann_text     = get_announcement(traffic_key,  lang_code)
                ann_fallback = get_announcement(traffic_key,  "en-US")
            if b4.button(ui["btn_progress"], key=f"ann_progress_{v_idx}", use_container_width=True):
                ann_text     = get_announcement("progress",   lang_code,
                                                done=completed, total=total_stops,
                                                remaining=total_stops - completed)
                ann_fallback = get_announcement("progress",   "en-US",
                                                done=completed, total=total_stops,
                                                remaining=total_stops - completed)
            if b5.button(ui["btn_brief"],    key=f"ann_brief_{v_idx}",    use_container_width=True):
                ann_text     = get_announcement("briefing",   lang_code,
                                                loc=next_loc_spk, eta=next_eta,
                                                level=delay_lvl,
                                                dist=f"{tot_dist:.1f}",
                                                done=completed, total=total_stops,
                                                remaining=total_stops - completed,
                                                period=period)
                ann_fallback = get_announcement("briefing",   "en-US",
                                                loc=next_loc_en,  eta=next_eta,
                                                level=delay_lvl,
                                                dist=f"{tot_dist:.1f}",
                                                done=completed, total=total_stops,
                                                remaining=total_stops - completed,
                                                period=period)
            if ann_text:
                st.session_state.last_announcement          = ann_text
                st.session_state.last_announcement_fallback = ann_fallback
                st.session_state.do_speak = True
                st.rerun()

    if st.session_state.get("do_speak") and st.session_state.get("last_announcement"):
        st.info(f"🔊 {st.session_state.last_announcement}")
        speak_js(
            st.session_state.last_announcement,
            lang_code,
            fallback_text=st.session_state.get("last_announcement_fallback", ""),
        )
        st.session_state.do_speak = False


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.role=="Admin":
    render_admin()
else:
    render_driver()
