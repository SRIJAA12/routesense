from sklearn.cluster import KMeans

def cluster_deliveries(df,k=3):

    coords = df[['lat','lon']]

    kmeans = KMeans(n_clusters=k,n_init=10)

    df["cluster"] = kmeans.fit_predict(coords)

    return df