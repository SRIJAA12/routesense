import random

def simulate_traffic(distance_matrix):

    i = random.randint(0,len(distance_matrix)-1)
    j = random.randint(0,len(distance_matrix)-1)

    distance_matrix[i][j] *= 1.8

    return distance_matrix