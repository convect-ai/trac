import requests


def deploy(
    endpoint,
    app_def_name,
    app_def_description,
    app_def_image_name,
    app_def_image_tag,
    app_inst_name,
    app_inst_description,
):
    if endpoint.endswith("/"):
        endpoint = endpoint.rstrip("/")
    # Create app definition
    app_def_endpoint = endpoint + "/api/apps/"

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
    app_inst_endpoint = endpoint + "/api/apps/" + str(app_def_id) + "/instances/"
    app_inst_data = {
        "name": app_inst_name,
        "description": app_inst_description,
    }

    app_inst_response = requests.post(app_inst_endpoint, json=app_inst_data)
    app_inst_response.raise_for_status()

    app_inst_id = app_inst_response.json()["id"]

    # return the app instance dashboard url
    return f"{endpoint}/instances/{app_inst_id}/dashboard/"


def undeploy(endpoint, app_def_id, app_inst_id):
    if endpoint.endswith("/"):
        endpoint = endpoint.rstrip("/")

    # delete app instance
    instance_delete_endpoint = (
        f"{endpoint}/api/apps/{app_def_id}/instances/{app_inst_id}"
    )
    resp = requests.delete(instance_delete_endpoint)
    resp.raise_for_status()

    # delete app definition
    app_def_delete_endpoint = f"{endpoint}/api/apps/{app_def_id}"
    resp = requests.delete(app_def_delete_endpoint)
    resp.raise_for_status()
