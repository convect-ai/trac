import json
import uuid
from typing import List

from apps.trac_app.models import AppInstance
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from trac.schema.task import FileDef

from .forms import DatasetForm
from .models import DataSet, Resource
from .schema_utils import generate_openapi_schema_for_dataset
from .services.gsheet import GoogleSheetsDataBackend


def create_dataset(request, instance_id):
    """
    Create a DataSet when request is POST
    """
    if request.method == "POST":
        form = DatasetForm(request.POST)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.app = AppInstance.objects.get(id=instance_id)
            # set the schema field of the dataset
            app = dataset.app
            # get the app_definition of the app
            app_def = app.app
            # get the schema of the app_def
            schema = {
                "input_schema": app_def.input_schema(),
                "output_schema": app_def.output_schema(),
            }
            dataset.schema = schema

            # if the dataset backend is gsheet, call the gsheet api to create a new spreadsheet
            uniq_identifier = str(uuid.uuid4())[:8]
            spreadsheet_name = dataset.name + "_" + uniq_identifier
            if dataset.backend == "gsheet":
                sheet_url = GoogleSheetsDataBackend.init_spreadsheet(
                    dataset.schema["input_schema"], spreadsheet_name=spreadsheet_name
                )

                dataset.url = sheet_url

            dataset.initialized = True

            dataset.save()
            return redirect("trac_app:dashboard", instance_id=instance_id)
    else:
        form = DatasetForm()
    return render(
        request,
        "data_gateway/create_dataset.html",
        {"form": form, "instance_id": instance_id},
    )


def update_dataset(request, instance_id, dataset_id):
    """
    Update a DataSet when request is PUT
    """
    dataset = DataSet.objects.get(id=dataset_id)
    if request.method == "POST":
        form = DatasetForm(request.POST, instance=dataset)
        if form.is_valid():

            new_dataset = form.save(commit=False)
            new_dataset.app = dataset.app
            # set the schema field of the dataset
            app = new_dataset.app
            # get the app_definition of the app
            app_def = app.app
            # get the schema of the app_def
            schema = {
                "input_schema": app_def.input_schema(),
                "output_schema": app_def.output_schema(),
            }
            new_dataset.schema = schema
            new_dataset.save()
            return redirect("trac_app:dashboard", instance_id=instance_id)
    else:
        form = DatasetForm(instance=dataset)
    return render(
        request,
        "data_gateway/create_dataset.html",
        {"form": form, "instance_id": instance_id},
    )


def delete_dataset(request, instance_id, dataset_id):
    """
    Delete a DataSet when request is DELETE
    """
    if request.method == "POST":
        dataset = DataSet.objects.get(id=dataset_id)
        dataset.delete()
        return redirect("trac_app:dashboard", instance_id=instance_id)


def dataset_input_view(request, instance_id, dataset_id):
    """
    Show a dataset input view when request is GET
    Render all the resources in the spreadsheet form
    """
    dataset = DataSet.objects.get(id=dataset_id)

    if dataset.backend == "gsheet":
        # redirect to the gsheet view in a new tab
        return redirect(dataset.url)

    input_schema: List[FileDef] = dataset.schema["input_schema"]

    workbook_data = []
    for resource_schema in input_schema:
        # resource_schema is a jsonschema that defines an object
        resource_name = resource_schema.name
        # header names
        field_names = list(resource_schema.file_schema["properties"].keys())
        # data
        resources = Resource.objects.filter(
            dataset=dataset, resource_type=resource_name
        ).all()

        celldata = []
        # header
        for idx, name in enumerate(field_names):
            celldata.append({"r": 0, "c": idx, "v": name})

        # data
        for idx, resource in enumerate(resources):
            for jdx, name in enumerate(field_names):
                celldata.append({"r": idx + 1, "c": jdx, "v": resource.value.get(name)})

        workbook_data.append({"name": resource_name, "celldata": celldata})

    context = {
        "workbook_data": json.dumps(workbook_data),
        "instance_id": instance_id,
        "dataset_id": dataset_id,
    }

    return render(request, "data_gateway/view_data.html", context=context)


def dataset_input_view_save(request, instance_id, dataset_id):
    """
    Update or create a resource when request is PUT or POST
    """
    # decide if the request is ajax
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        if request.method == "POST":
            # get data schema
            dataset = DataSet.objects.get(id=dataset_id)
            input_schema = dataset.schema["input_schema"]

            payload = json.loads(request.POST["data"])
            # TODO: validate the payload
            resources_to_add = []
            for sheet in payload:
                sheet_name = sheet["name"]
                # get the schema with title == sheet_name
                resource_schema = next(
                    (x for x in input_schema if x.name == sheet_name), None
                )
                field_names = list(resource_schema.file_schema["properties"].keys())
                cell_data = sheet["data"]
                # drop the first row
                cell_data = cell_data[1:]

                for idx, row in enumerate(cell_data):
                    resource_value = {}
                    for jidx, cell in enumerate(row):
                        if not cell:
                            break
                        field_name = field_names[jidx]
                        value = cell["v"]
                        resource_value[field_name] = value

                    # construct a resource
                    resource = Resource(
                        dataset=dataset, resource_type=sheet_name, value=resource_value
                    )

                    resources_to_add.append(resource)

            # start a transaction
            with transaction.atomic():
                # TODO: this is very inefficient
                # delete all the resources
                Resource.objects.filter(dataset=dataset).delete()
                # add all the resources
                Resource.objects.bulk_create(resources_to_add)
            # get the number of resources impacted
            num_resources = len(resources_to_add)

            return HttpResponse("OK. {} resources added".format(num_resources))

    else:
        return HttpResponse(status=400, reason="Bad Request")


def dataset_api_spec(request, dataset_id):
    """
    Generate a swagger spec for a dataset
    """
    dataset = DataSet.objects.get(id=dataset_id)
    oas_schema = generate_openapi_schema_for_dataset(dataset)

    # return a json response wrapping the oas_schema
    return JsonResponse(oas_schema)


def dataset_api_swagger_ui(request, dataset_id):
    """
    Return a swagger UI that renders the spec
    """
    return render(
        request,
        "data_gateway/swagger_ui.html",
        {
            "schema_url": reverse("data_gateway:dataset_api_spec", args=[dataset_id]),
        },
    )
