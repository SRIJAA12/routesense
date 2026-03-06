import time
import numpy as np
import pandas as pd
import streamlit as st
import folium
import plotly.express as px
from sklearn.cluster import KMeans
from streamlit_folium import st_folium
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


st.set_page_config(page_title="Adaptive Logistics Routing System", layout="wide")


def apply_theme(theme_mode: str) -> None:
    if theme_mode == "Light Mode":
        st.markdown(
            """
            <style>
            .stApp {background-color: #FFFFFF; color: #0F172A;}
            .stMetric {background-color: #F1F5F9; border-radius: 10px; padding: 12px;}
            .stButton > button {
                background-color: #1D4ED8;
                color: #FFFFFF;
                border: 0;
                border-radius: 8px;
                width: 100%;
            }
            h1, h2, h3 {color: #1E3A8A;}
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .stApp {background-color: #0B1220; color: #FFFFFF;}
            .stMetric {background-color: #111827; border-radius: 10px; padding: 12px;}
            .stButton > button {
                background-color: #2563EB;
                color: #FFFFFF;
                border: 0;
                border-radius: 8px;
                width: 100%;
            }
            h1, h2, h3 {color: #DBEAFE;}
            </style>
            """,
            unsafe_allow_html=True,
        )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return earth_radius_km * c


def generate_synthetic_deliveries(seed: int = 42, n_deliveries: int = 12) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    depot_lat, depot_lon = 13.0827, 80.2707

    records = [
        {
            "id": 0,
            "location": "Depot",
            "lat": depot_lat,
            "lon": depot_lon,
            "type": "depot",
        }
    ]

    for index in range(1, n_deliveries + 1):
        records.append(
            {
                "id": index,
                "location": f"Delivery {index:02d}",
                "lat": depot_lat + rng.uniform(-0.06, 0.06),
                "lon": depot_lon + rng.uniform(-0.06, 0.06),
                "type": "delivery",
            }
        )

    return pd.DataFrame(records)


def cluster_deliveries(df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    clustered = df.copy()
    delivery_mask = clustered["type"] == "delivery"

    model = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    clustered.loc[delivery_mask, "cluster"] = model.fit_predict(
        clustered.loc[delivery_mask, ["lat", "lon"]]
    )
    clustered["cluster"] = clustered["cluster"].fillna(-1).astype(int)
    return clustered


def create_distance_matrix(df: pd.DataFrame) -> np.ndarray:
    coordinates = df[["lat", "lon"]].to_numpy()
    size = len(coordinates)
    distance_matrix = np.zeros((size, size))

    for i in range(size):
        for j in range(size):
            if i == j:
                distance_matrix[i, j] = 0
            else:
                distance_matrix[i, j] = haversine_km(
                    coordinates[i][0],
                    coordinates[i][1],
                    coordinates[j][0],
                    coordinates[j][1],
                )
    return distance_matrix


def optimize_route_vrp(distance_matrix: np.ndarray) -> tuple[list[int], float]:
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 1000)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 2

    solution = routing.SolveWithParameters(search_parameters)
    if solution is None:
        return [], 0.0

    route_indices: list[int] = []
    route_distance_m = 0
    index = routing.Start(0)

    while not routing.IsEnd(index):
        route_indices.append(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance_m += routing.GetArcCostForVehicle(previous_index, index, 0)

    route_indices.append(manager.IndexToNode(index))
    return route_indices, route_distance_m / 1000.0


def sequential_route_distance(distance_matrix: np.ndarray) -> float:
    index_path = list(range(distance_matrix.shape[0])) + [0]
    distance = 0.0
    for idx in range(len(index_path) - 1):
        distance += distance_matrix[index_path[idx], index_path[idx + 1]]
    return float(distance)


def apply_traffic_disruption(distance_matrix: np.ndarray) -> np.ndarray:
    updated = distance_matrix.copy()
    size = len(updated)
    node_i, node_j = np.random.randint(1, size, size=2)

    while node_i == node_j:
        node_j = np.random.randint(1, size)

    disruption_multiplier = np.random.uniform(1.4, 1.9)
    updated[node_i, node_j] *= disruption_multiplier
    updated[node_j, node_i] *= disruption_multiplier
    return updated


def build_route_map(df: pd.DataFrame, route: list[int] | None, vehicle_index: int | None) -> folium.Map:
    map_center = [df["lat"].mean(), df["lon"].mean()]
    route_map = folium.Map(location=map_center, zoom_start=12, control_scale=True)

    for _, row in df.iterrows():
        marker_color = "blue"
        popup_text = row["location"]
        if "cluster" in df.columns and row["cluster"] >= 0:
            popup_text = f"{popup_text} | Cluster {row['cluster']}"

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            color=marker_color,
            fill=True,
            fill_opacity=0.95,
            popup=popup_text,
        ).add_to(route_map)

    if route:
        route_points = [[df.iloc[node]["lat"], df.iloc[node]["lon"]] for node in route]
        folium.PolyLine(route_points, color="blue", weight=5, opacity=0.9).add_to(route_map)

        if vehicle_index is not None and 0 <= vehicle_index < len(route):
            vehicle_node = route[vehicle_index]
            folium.Marker(
                [df.iloc[vehicle_node]["lat"], df.iloc[vehicle_node]["lon"]],
                icon=folium.Icon(color="red", icon="truck", prefix="fa"),
                popup="Vehicle Position",
            ).add_to(route_map)

    return route_map


def initialize_state() -> None:
    if "deliveries" not in st.session_state:
        st.session_state.deliveries = generate_synthetic_deliveries()

    if "route" not in st.session_state:
        st.session_state.route = None

    if "vehicle_index" not in st.session_state:
        st.session_state.vehicle_index = 0

    if "route_distance" not in st.session_state:
        st.session_state.route_distance = 0.0

    if "baseline_distance" not in st.session_state:
        base_matrix = create_distance_matrix(st.session_state.deliveries)
        st.session_state.baseline_distance = sequential_route_distance(base_matrix)

    if "status_message" not in st.session_state:
        st.session_state.status_message = "System ready"


initialize_state()

st.sidebar.title("Controls")
theme = st.sidebar.selectbox("Theme", ["Light Mode", "Dark Mode"])
apply_theme(theme)

generate_route_clicked = st.sidebar.button("Generate Route")
cluster_clicked = st.sidebar.button("Cluster Deliveries")
traffic_clicked = st.sidebar.button("Simulate Traffic")
simulate_vehicle_clicked = st.sidebar.button("Start Vehicle Simulation")

if cluster_clicked:
    st.session_state.deliveries = cluster_deliveries(st.session_state.deliveries)
    st.session_state.status_message = "Delivery clusters updated"

if generate_route_clicked:
    base_matrix = create_distance_matrix(st.session_state.deliveries)
    st.session_state.baseline_distance = sequential_route_distance(base_matrix)
    optimized_route, optimized_distance = optimize_route_vrp(base_matrix)
    st.session_state.route = optimized_route
    st.session_state.route_distance = optimized_distance
    st.session_state.vehicle_index = 0
    st.session_state.status_message = "Optimized route generated"

if traffic_clicked:
    current_matrix = create_distance_matrix(st.session_state.deliveries)
    disrupted_matrix = apply_traffic_disruption(current_matrix)
    rerouted_path, rerouted_distance = optimize_route_vrp(disrupted_matrix)
    st.session_state.route = rerouted_path
    st.session_state.route_distance = rerouted_distance
    st.session_state.vehicle_index = 0
    st.session_state.status_message = "Traffic disruption detected. Route re-optimized."

st.title("Adaptive Logistics Routing System")

if st.session_state.status_message:
    st.info(st.session_state.status_message)

control_tab, driver_tab, analytics_tab = st.tabs(["Control Tower", "Driver View", "Analytics"])

with control_tab:
    deliveries_df = st.session_state.deliveries
    total_deliveries = int((deliveries_df["type"] == "delivery").sum())
    fleet_size = 1
    route_status = "Optimized" if st.session_state.route else "Pending"
    distance_savings = max(st.session_state.baseline_distance - st.session_state.route_distance, 0.0)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Deliveries", total_deliveries)
    m2.metric("Fleet Size", fleet_size)
    m3.metric("Route Status", route_status)
    m4.metric("Estimated Distance Savings", f"{distance_savings:.2f} km")

    map_placeholder = st.empty()
    control_map = build_route_map(
        deliveries_df,
        st.session_state.route,
        st.session_state.vehicle_index if st.session_state.route else None,
    )
    with map_placeholder.container():
        st_folium(control_map, width=None, height=560, use_container_width=True)

    if simulate_vehicle_clicked and st.session_state.route:
        for index in range(len(st.session_state.route)):
            st.session_state.vehicle_index = index
            animated_map = build_route_map(
                deliveries_df,
                st.session_state.route,
                st.session_state.vehicle_index,
            )
            with map_placeholder.container():
                st_folium(animated_map, width=None, height=560, use_container_width=True)
            time.sleep(1)

with driver_tab:
    st.subheader("Driver Interface")
    if not st.session_state.route:
        st.warning("No optimized route available. Generate Route from the sidebar.")
    else:
        route_nodes = st.session_state.route
        vehicle_idx = min(st.session_state.vehicle_index, len(route_nodes) - 1)
        next_node = route_nodes[min(vehicle_idx + 1, len(route_nodes) - 1)]

        left_col, right_col = st.columns([1, 2])

        with left_col:
            st.metric("Current Next Stop", st.session_state.deliveries.iloc[next_node]["location"])
            stop_sequence = [
                st.session_state.deliveries.iloc[node]["location"]
                for node in route_nodes
                if node != 0
            ]
            st.write("Delivery Stops")
            st.dataframe(pd.DataFrame({"Stop": stop_sequence}), use_container_width=True, height=420)

        with right_col:
            driver_map = build_route_map(st.session_state.deliveries, route_nodes, vehicle_idx)
            st_folium(driver_map, width=None, height=560, use_container_width=True)

with analytics_tab:
    st.subheader("Analytics Dashboard")
    before_distance = st.session_state.baseline_distance
    after_distance = st.session_state.route_distance if st.session_state.route else before_distance
    saved_distance = max(before_distance - after_distance, 0.0)

    chart_df = pd.DataFrame(
        {
            "Route": ["Before Optimization", "After Optimization"],
            "Distance (km)": [before_distance, after_distance],
        }
    )
    figure = px.bar(
        chart_df,
        x="Route",
        y="Distance (km)",
        color="Route",
        text="Distance (km)",
        color_discrete_sequence=["#60A5FA", "#1D4ED8"],
    )
    figure.update_layout(showlegend=False, height=420, margin=dict(l=10, r=10, t=10, b=10))
    figure.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    st.plotly_chart(figure, use_container_width=True)

    fuel_savings = saved_distance * 0.18
    delivery_efficiency = 0.0 if before_distance == 0 else (saved_distance / before_distance) * 100

    a1, a2, a3 = st.columns(3)
    a1.metric("Distance Saved", f"{saved_distance:.2f} km")
    a2.metric("Estimated Fuel Savings", f"{fuel_savings:.2f} L")
    a3.metric("Delivery Efficiency", f"{delivery_efficiency:.1f}%")