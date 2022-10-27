# deploy an app image to the trac ui server

import json

import requests


def deploy(
    server_endpoint,
    app_def_name,
    app_def_description,
    app_def_image_name,
    app_def_image_tag,
    app_inst_description,
):
    if server_endpoint.endswith("/"):
        server_endpoint = server_endpoint.rstrip("/")
    # Create app definition
    app_def_endpoint = server_endpoint + "/api/apps/"

    app_def_data = {
        "name": app_def_name,
        "description": app_def_description,
        "image_name": app_def_image_name,
        "image_tag": app_def_image_tag,
    }

    app_def_response = requests.post(app_def_endpoint, json=app_def_data)
    app_def_response.raise_for_status()

    app_def_id = app_def_response.json()["id"]

    # create app instance
    app_inst_endpoint = server_endpoint + "/api/apps/" + str(app_def_id) + "/instances/"
    app_inst_data = {
        "name": app_def_name + " instance",
        "description": app_inst_description,
    }

    app_inst_response = requests.post(app_inst_endpoint, json=app_inst_data)
    app_inst_response.raise_for_status()

    app_inst_id = app_inst_response.json()["id"]

    # write the above information to a file .trac.deploy.json for future use
    dashboard_url = f"{server_endpoint}/instances/{app_inst_id}/dashboard/"
    with open(".trac.deploy.json", "w") as f:
        f.write(
            json.dumps(
                {
                    "app_image_name": app_def_image_name,
                    "app_image_tag": app_def_image_tag,
                    "app_def_id": app_def_id,
                    "app_inst_id": app_inst_id,
                    "server_endpoint": server_endpoint,
                    "dashboard_url": dashboard_url,
                }
            )
        )

    # return the app instance dashboard url
    return dashboard_url


def undeploy(server_endpoint, app_def_id=None, app_inst_id=None):
    if server_endpoint.endswith("/"):
        server_endpoint = server_endpoint.rstrip("/")

    if not app_def_id or not app_inst_id:
        # read .trac.deploy.json for the variable values
        # check if the file exists
        try:
            with open(".trac.deploy.json", "r") as f:
                data = json.load(f)
                app_def_id = data["app_def_id"]
                app_inst_id = data["app_inst_id"]
        except FileNotFoundError:
            raise Exception(
                "No .trac.deploy.json file found. Please provide app_def_id and app_inst_id"
            )

    # delete app instance
    instance_delete_endpoint = (
        f"{server_endpoint}/api/apps/{app_def_id}/instances/{app_inst_id}"
    )
    resp = requests.delete(instance_delete_endpoint)
    resp.raise_for_status()

    # delete app definition
    app_def_delete_endpoint = f"{server_endpoint}/api/apps/{app_def_id}"
    resp = requests.delete(app_def_delete_endpoint)
    resp.raise_for_status()
