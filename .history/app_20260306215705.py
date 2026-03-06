import streamlit as st
import pandas as pd
import numpy as np
import time
import folium
from streamlit_folium import st_folium
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import plotly.express as px
from sklearn.cluster import KMeans


# ------------------------------
# PAGE CONFIG
# ------------------------------

st.set_page_config(page_title="Adaptive Routing", layout="wide")


# ------------------------------
# THEME
# ------------------------------

theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])

if theme == "Light":

    st.markdown("""
    <style>
    .main {
        background-color:#F7FAFC;
    }
    h1,h2,h3 {
        color:#1E3A8A;
    }
    .stButton>button {
        background-color:#2563EB;
        color:white;
        border-radius:8px;
    }
    </style>
    """, unsafe_allow_html=True)

else:

    st.markdown("""
    <style>
    .main {
        background-color:#0E1117;
        color:white;
    }
    </style>
    """, unsafe_allow_html=True)


# ------------------------------
# SESSION STATE
# ------------------------------

if "route" not in st.session_state:
    st.session_state.route = None

if "vehicle_pos" not in st.session_state:
    st.session_state.vehicle_pos = 0


# ------------------------------
# SYNTHETIC DATA
# ------------------------------

def generate_data():

    locations = [
        "Depot","T Nagar","Velachery","Tambaram",
        "Anna Nagar","Adyar","Porur","Guindy",
        "OMR","Perambur","Mylapore","Sholinganallur"
    ]

    lat_base = 13.0827
    lon_base = 80.2707

    rows = []

    for i in range(len(locations)):

        lat = lat_base + np.random.uniform(-0.05,0.05)
        lon = lon_base + np.random.uniform(-0.05,0.05)

        rows.append({
            "id":i,
            "location":locations[i],
            "lat":lat,
            "lon":lon
        })

    return pd.DataFrame(rows)


data = generate_data()


# ------------------------------
# CLUSTERING
# ------------------------------

def cluster_locations(df):

    coords = df[['lat','lon']]

    kmeans = KMeans(n_clusters=3,n_init=10)

    df["cluster"] = kmeans.fit_predict(coords)

    return df


# ------------------------------
# DISTANCE MATRIX
# ------------------------------

def create_distance_matrix(df):

    coords = df[['lat','lon']].values

    size = len(coords)

    matrix = np.zeros((size,size))

    for i in range(size):
        for j in range(size):

            dx = coords[i][0] - coords[j][0]
            dy = coords[i][1] - coords[j][1]

            matrix[i][j] = ((dx**2 + dy**2)**0.5)*111

    return matrix


# ------------------------------
# ROUTE OPTIMIZER
# ------------------------------

def optimize_route(distance_matrix):

    manager = pywrapcp.RoutingIndexManager(len(distance_matrix),1,0)

    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index,to_index):

        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)

        return int(distance_matrix[from_node][to_node]*100)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    route = []

    if solution:

        index = routing.Start(0)

        while not routing.IsEnd(index):

            route.append(manager.IndexToNode(index))

            index = solution.Value(routing.NextVar(index))

        route.append(manager.IndexToNode(index))

    return route


# ------------------------------
# TRAFFIC SIMULATION
# ------------------------------

def simulate_traffic(matrix):

    i = np.random.randint(0,len(matrix))
    j = np.random.randint(0,len(matrix))

    matrix[i][j] *= 1.8

    return matrix


# ------------------------------
# MAP DISPLAY
# ------------------------------

def show_map(df,route=None,vehicle_index=None):

    center = [df.lat.mean(),df.lon.mean()]

    m = folium.Map(location=center,zoom_start=12)

    for _,row in df.iterrows():

        folium.CircleMarker(
            location=[row.lat,row.lon],
            radius=6,
            color="blue",
            fill=True
        ).add_to(m)

    if route:

        points = []

        for r in route:
            points.append([df.iloc[r].lat,df.iloc[r].lon])

        folium.PolyLine(points,color="blue",weight=5).add_to(m)

        if vehicle_index is not None and vehicle_index < len(route):

            v = route[vehicle_index]

            folium.Marker(
                [df.iloc[v].lat,df.iloc[v].lon],
                icon=folium.Icon(color="red")
            ).add_to(m)

    st_folium(m,width=900)


# ------------------------------
# TITLE
# ------------------------------

st.title("Adaptive Logistics Routing")


# ------------------------------
# TABS
# ------------------------------

tab1, tab2, tab3 = st.tabs([
    "Control Tower",
    "Driver View",
    "Analytics"
])


# ------------------------------
# CONTROL TOWER
# ------------------------------

with tab1:

    st.subheader("Operations Dashboard")

    col1,col2,col3 = st.columns(3)

    col1.metric("Deliveries", len(data))
    col2.metric("Fleet", 3)
    col3.metric("Status", "Active")

    show_map(data, st.session_state.route, st.session_state.vehicle_pos)

    col1,col2,col3 = st.columns(3)

    if col1.button("Cluster Deliveries"):

        data = cluster_locations(data)
        st.success("Locations grouped")

    if col2.button("Generate Route"):

        matrix = create_distance_matrix(data)
        st.session_state.route = optimize_route(matrix)

    if col3.button("Simulate Traffic"):

        matrix = create_distance_matrix(data)
        matrix = simulate_traffic(matrix)

        st.session_state.route = optimize_route(matrix)

        st.warning("Traffic detected. Route updated")


    if st.button("Start Vehicle Simulation"):

        if st.session_state.route:

            for i in range(len(st.session_state.route)):

                st.session_state.vehicle_pos = i

                show_map(data, st.session_state.route, i)

                time.sleep(1)


# ------------------------------
# DRIVER VIEW
# ------------------------------

with tab2:

    st.subheader("Driver Navigation")

    if st.session_state.route:

        st.write("Delivery Sequence")

        for r in st.session_state.route:

            st.write(data.iloc[r]["location"])

        show_map(data, st.session_state.route)

    else:

        st.info("Generate route from Control Tower")


# ------------------------------
# ANALYTICS
# ------------------------------

with tab3:

    st.subheader("Route Analytics")

    before = 120
    after = 102

    col1,col2 = st.columns(2)

    col1.metric("Distance Before", f"{before} km")
    col2.metric("Distance After", f"{after} km")

    df_chart = pd.DataFrame({
        "Metric":["Before","After"],
        "Distance":[before,after]
    })

    fig = px.bar(df_chart,x="Metric",y="Distance",color="Metric")

    st.plotly_chart(fig,use_container_width=True)