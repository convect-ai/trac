import json

import pandas as pd


def read_location():
    df = pd.read_csv("data/locations.csv")
    return df


def compute_distance(df_location):
    """
    Given a location dataframe, compute the distance matrix using manhattan distance
    """
    # Compute distance matrix
    distance_matrix = []
    for i in range(len(df_location)):
        distance_matrix.append([])
        for j in range(len(df_location)):
            dist = abs(
                df_location.iloc[i]["x_cord"] - df_location.iloc[j]["x_cord"]
            ) + abs(df_location.iloc[i]["y_cord"] - df_location.iloc[j]["y_cord"])
            distance_matrix[i].append(dist / 100)
    return distance_matrix


def read_time_windows():
    df = pd.read_csv("data/time_window.csv")
    return df


def read_parameters():
    with open("data/parameters.json") as f:
        data = json.load(f)

    return data


# [START data_model]
def create_data_model():
    """Stores the data for the problem."""

    df_location = read_location()
    df_time_windows = read_time_windows()
    params = read_parameters()

    data = {}
    data["time_matrix"] = compute_distance(df_location)
    data["time_windows"] = df_time_windows.drop("location", axis=1).values.tolist()
    data["num_vehicles"] = params.get("num_vehicles", 4)
    data["depot"] = params.get("depot", 0)
    print(data)
    return data
    # [END data_model]
