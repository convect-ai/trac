# Copied from https://github.com/google/or-tools/blob/stable/ortools/constraint_solver/samples/vrp_time_windows.py


#!/usr/bin/env python3
# Copyright 2010-2022 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START program]
"""Vehicles Routing Problem (VRP) with Time Windows."""

# [START import]
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from vrp_demo_script.utils import create_data_model

# [END import]


# [START solution_printer]
def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()}")
    time_dimension = routing.GetDimensionOrDie("Time")
    total_time = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += "{0} Time({1},{2}) -> ".format(
                manager.IndexToNode(index),
                solution.Min(time_var),
                solution.Max(time_var),
            )
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        plan_output += "{0} Time({1},{2})\n".format(
            manager.IndexToNode(index), solution.Min(time_var), solution.Max(time_var)
        )
        plan_output += "Time of the route: {}min\n".format(solution.Min(time_var))
        print(plan_output)
        total_time += solution.Min(time_var)
    print("Total time of all routes: {}min".format(total_time))
    # [END solution_printer]


def write_solution_to_csv(data, manager, routing, solution):
    """Writes solution to csv file."""
    time_dimension = routing.GetDimensionOrDie("Time")
    with open("data/solution.csv", "w") as f:
        f.write("vehicle_id,location_id,arrival_time,departure_time\n")
        for vehicle_id in range(data["num_vehicles"]):
            index = routing.Start(vehicle_id)
            while not routing.IsEnd(index):
                time_var = time_dimension.CumulVar(index)
                f.write(
                    "{0},{1},{2},{3}\n".format(
                        vehicle_id,
                        manager.IndexToNode(index),
                        solution.Min(time_var),
                        solution.Max(time_var),
                    )
                )
                index = solution.Value(routing.NextVar(index))
            time_var = time_dimension.CumulVar(index)
            f.write(
                "{0},{1},{2},{3}\n".format(
                    vehicle_id,
                    manager.IndexToNode(index),
                    solution.Min(time_var),
                    solution.Max(time_var),
                )
            )


def main():
    """Solve the VRP with time windows."""
    # Instantiate the data problem.
    # [START data]
    data = create_data_model()
    # [END data]

    # Create the routing index manager.
    # [START index_manager]
    manager = pywrapcp.RoutingIndexManager(
        len(data["time_matrix"]), data["num_vehicles"], data["depot"]
    )
    # [END index_manager]

    # Create Routing Model.
    # [START routing_model]
    routing = pywrapcp.RoutingModel(manager)

    # [END routing_model]

    # Create and register a transit callback.
    # [START transit_callback]
    def time_callback(from_index, to_index):
        """Returns the travel time between the two nodes."""
        # Convert from routing variable Index to time matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["time_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    # [END transit_callback]

    # Define cost of each arc.
    # [START arc_cost]
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    # [END arc_cost]

    # Add Time Windows constraint.
    # [START time_windows_constraint]
    time = "Time"
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time
        30,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time,
    )
    time_dimension = routing.GetDimensionOrDie(time)
    # Add time window constraints for each location except depot.
    for location_idx, time_window in enumerate(data["time_windows"]):
        if location_idx == data["depot"]:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
    # Add time window constraints for each vehicle start node.
    depot_idx = data["depot"]
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(
            data["time_windows"][depot_idx][0], data["time_windows"][depot_idx][1]
        )
    # [END time_windows_constraint]

    # Instantiate route start and end times to produce feasible times.
    # [START depot_start_end_times]
    for i in range(data["num_vehicles"]):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i))
        )
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(i)))
    # [END depot_start_end_times]

    # Setting first solution heuristic.
    # [START parameters]
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    # [END parameters]

    # Solve the problem.
    # [START solve]
    solution = routing.SolveWithParameters(search_parameters)
    # [END solve]

    # Print solution on console.
    # [START print_solution]
    if solution:
        print_solution(data, manager, routing, solution)
        write_solution_to_csv(data, manager, routing, solution)
    else:
        print("No solution found !")
    # [END print_solution]


if __name__ == "__main__":
    main()
# [END program]
