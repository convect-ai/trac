# also load: _hourly, _monthly, _weekly, _yearly, or _live_daily
import json

import pandas as pd
from autots import AutoTS

date_col = "datetime"
value_col = "value"
id_col = "series_id"


def load_parameters():
    parameter_path = "data/parameters.json"
    with open(parameter_path) as f:
        parameters = json.load(f)

    return parameters


def load_data():
    data_path = "data/ts.csv"
    df = pd.read_csv(data_path, parse_dates=True)
    return df


def run_autots(df, parameters):
    model = AutoTS(
        forecast_length=parameters["forecast_length"],
        frequency="infer",
        ensemble=None,  # TODO: add ensemble to the parameters
        model_list=parameters["model_list"],
        transformer_list=parameters["transformer_list"],
        prediction_interval=parameters["prediction_interval"],
        drop_most_recent=parameters["drop_most_recent"],
        num_validations=parameters["num_validations"],
        validation_method=parameters["validation_method"],
    )
    model = model.fit(df, date_col=date_col, value_col=value_col, id_col=id_col)
    return model


def print_model_summary(model):
    model_results = model.results
    validation_results = model.results("validation")

    print("Model Summary")
    print("=============")
    print(model_results)

    print("Validation Results")
    print("==================")
    print(validation_results)


def write_predictions(model):
    forecast = model.predict()
    forecast.long_form_results().to_csv("data/output/forecast.csv", index=False)


def main():
    parameters = load_parameters()
    df = load_data()
    model = run_autots(df, parameters)
    print_model_summary(model)
    write_predictions(model)


if __name__ == "__main__":
    main()
