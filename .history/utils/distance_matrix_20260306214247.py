import numpy as np

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