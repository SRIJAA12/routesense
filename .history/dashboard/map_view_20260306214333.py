import folium
from streamlit_folium import st_folium

def show_map(df,route=None):

    center = [df.lat.mean(),df.lon.mean()]

    m = folium.Map(location=center,zoom_start=12)

    for _,row in df.iterrows():

        folium.Marker(
            location=[row.lat,row.lon],
            popup=row.location
        ).add_to(m)

    if route:

        points = []

        for r in route:
            points.append([df.iloc[r].lat,df.iloc[r].lon])

        folium.PolyLine(points,color="blue",weight=5).add_to(m)

    st_folium(m,width=700)