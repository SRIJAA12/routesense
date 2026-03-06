import pandas as pd
import numpy as np

np.random.seed(42)

locations = [
    "Chennai Depot","T Nagar","Velachery","Tambaram",
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
        "lon":lon,
        "demand":np.random.randint(1,4)
    })

df = pd.DataFrame(rows)

df.to_csv("data/deliveries.csv",index=False)

fleet = pd.DataFrame({
    "vehicle_id":["Truck1","Truck2","Truck3"],
    "capacity":[8,8,8]
})

fleet.to_csv("data/fleet.csv",index=False)

print("Synthetic dataset generated")