from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def optimize_route(distance_matrix):

    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix),1,0)

    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index,to_index):

        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)

        return int(distance_matrix[from_node][to_node]*100)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    solution = routing.SolveWithParameters(search_parameters)

    route = []

    if solution:

        index = routing.Start(0)

        while not routing.IsEnd(index):

            route.append(manager.IndexToNode(index))

            index = solution.Value(routing.NextVar(index))

        route.append(manager.IndexToNode(index))

    return route