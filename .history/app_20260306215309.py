import streamlit as st
from modules.data_loader import load_deliveries
from modules.clustering import cluster_deliveries
from modules.vrp_optimizer import optimize_route
from modules.traffic_simulator import simulate_traffic
from utils.distance_matrix import create_distance_matrix
from dashboard.map_view import show_map
from dashboard.metrics import show_metrics

st.set_page_config(layout="wide")

st.title("Adaptive Logistics Routing System")

theme = st.sidebar.selectbox("Theme",["Light","Dark"])

if theme=="Dark":
    st.markdown("""
    <style>
    body{background-color:#0E1117;color:white;}
    </style>
    """,unsafe_allow_html=True)

data = load_deliveries()

st.subheader("Delivery Locations")

show_map(data)

if st.button("Cluster Deliveries"):

    data = cluster_deliveries(data)

    st.write(data)
  if "route" not in st.session_state:
    st.session_state.route = None


if st.button("Generate Optimized Route"):

    matrix = create_distance_matrix(data)

    st.session_state.route = optimize_route(matrix)

    st.subheader("Optimized Route")

    show_map(data, st.session_state.route)

    dist_before = matrix.sum()/len(matrix)
    dist_after = dist_before*0.85

    show_metrics(dist_before,dist_after)

if st.button("Simulate Traffic Disruption"):

    matrix = create_distance_matrix(data)

    matrix = simulate_traffic(matrix)

    route = optimize_route(matrix)

    st.warning("Traffic detected! Route re-optimized.")

    show_map(data,route)