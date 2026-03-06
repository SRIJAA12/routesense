import pandas as pd

def load_deliveries():
    return pd.read_csv("data/deliveries.csv")

def load_fleet():
    return pd.read_csv("data/fleet.csv")