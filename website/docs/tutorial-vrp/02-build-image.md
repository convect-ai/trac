---
title: Build an application image

---

# Build an application image


## Declare the input/output of your solution

After the scripts can run without any problem locally, then one need to define the inputs and outputs formats the scripts take in and generate.
TRAC will use this information to automatically render a UI and API suite for your application.

For example, let's assume your script takes in a file in the following format

| location | x_cord  | y_cord |
| ---------| --------| -------|
|location-0| 456     | 320    |
|location-1|228      |0       |
|location-2|912      |0       |
|location-3|0        |80      |

Then you can define the format for the file as

```json
{
    "name": "locations",
    "mount_path": "data/locations.csv",
    "type": "input",
    "description": "Locations to visit",
    "file_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "Location name"
            },
            "x_cord": {
                "type": "number",
                "description": "X coordinate"
            },
            "y_cord": {
                "type": "number",
                "description": "Y coordinate"
            }
        }
    }
}
```

## Declare the parameter of your solution

Parameters control the behavior of your scripts. For example, in a machine learning model, parameters can be the learning rate of the model.
To define a parameter your app can accept, use the following format

```json
{
    "parameter": {
        "mount_path": "data/parameters.json",
        "parameters": [
            {
                "name": "num_vehicles",
                "type": "integer",
                "description": "Number of vehicles in the fleet",
                "default": 4
            },
            {
                "name": "depot",
                "type": "integer",
                "description": "Depot location",
                "default": 0
            }
        ]
    }
}
```
In the above example, we define two integer type parameters.

## Declare the exposed functions of your solution

The last step is to define the entry point to your scripts -- what function to trigger when your main logic is invoked.

```json
{
    "handler": {
        "handler": "vrp_demo_script.main:main"
    }
}
```

The above defines the entry point as the `main` function under `vrp_demo_script.main` module.

This is a full example of [`trac.json`](https://github.com/convect-ai/trac/blob/master/examples/vrp-demo-script/trac.json).


## Build the image

You can trigger the building process by


```bash
trac-cli build examples/vrp-demo-script/ --image-name vrp-algo
```

This will build a docker image named `vrp-algo`.
You can verify if the image will successfully run by
```bash
docker run --rm vrp-algo -- spec
```
This will print out the contents of the `trac.json` defined earlier.
