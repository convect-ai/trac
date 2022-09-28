import json

import nbconvert
import nbformat
from apps.trac_app.models import AppDefinition, AppInstance
from django.http import HttpResponse
from django.shortcuts import redirect, render
from runtime.local import RuntimeFactory

from .forms import create_form_from_parameter_schema
from .models import AppRun


def list_runs(request, instance_id):
    """
    Show a list of runs under an app instance when request is GET
    """
    runs = AppRun.objects.filter(app__pk=instance_id).all()
    return render(
        request, "app_run/list_runs.html", {"runs": runs, "instance_id": instance_id}
    )


def create_run(request, instance_id):
    """
    Create a run under an app instance when request is POST
    """
    # get the app_def from the instance_id
    app = AppInstance.objects.get(id=instance_id)
    app_def = app.app
    # get the app_def's parameter schema

    runtime = RuntimeFactory.get_runtime()
    parameter_schema = runtime.spec(
        image_name=app_def.image_name,
        image_tag=app_def.image_tag,
    )

    form_cls = create_form_from_parameter_schema(parameter_schema, instance_id)

    if request.method == "POST":
        form = form_cls(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # create a new app run
            app_run = AppRun.objects.create(
                name=data["name"],
                description=data["description"],
                app=app,
                dataset=data["dataset"],
                parameters=data["parameters"],
            )

            # run the app
            nb = runtime.run(
                image_name=app_def.image_name,
                image_tag=app_def.image_tag,
                parameters=data["parameters"],
                dataset=data["dataset"],
            )

            app_run.output_artifacts = nb
            app_run.status = "COMPLETED"
            app_run.save()
            return redirect("app_run:list_runs", instance_id=instance_id)

    else:
        form = form_cls()

    return render(
        request, "app_run/create_run.html", {"form": form, "instance_id": instance_id}
    )


def update_run(request, instance_id, run_id):
    """
    Update a run under an app instance when request is PUT
    """
    # get the parameter_schema from the app_def
    # get the app_def from the instance_id
    app = AppInstance.objects.get(id=instance_id)
    app_def = app.app
    # get the app_def's parameter schema
    runtime = RuntimeFactory.get_runtime()
    parameter_schema = runtime.spec(
        image_name=app_def.image_name,
        image_tag=app_def.image_tag,
    )

    form_cls = create_form_from_parameter_schema(parameter_schema, instance_id)

    if request.method == "POST":
        form = form_cls(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # create a new app run
            app_run = AppRun.objects.create(
                name=data["name"],
                description=data["description"],
                app=app,
                dataset=data["dataset"],
                parameters=data["parameters"],
            )
            return redirect("app_run:list_runs", instance_id=instance_id)

    else:
        form = form_cls()
        # prepopulate the form with the existing data
        app_run = AppRun.objects.get(id=run_id)
        form.fields["name"].initial = app_run.name
        form.fields["description"].initial = app_run.description
        form.fields["dataset"].initial = app_run.dataset
        # for fields in app_run.parameters, set the initial value
        for field, value in app_run.parameters.items():
            form.fields[field].initial = value

    return render(
        request,
        "app_run/create_run.html",
        {"form": form, "run_id": run_id, "instance_id": instance_id},
    )


def delete_run(request, instance_id, run_id):
    """
    Delete a run under an app instance when request is DELETE
    """
    if request.method == "POST":
        app_run = AppRun.objects.get(id=run_id)
        app_run.delete()
        return redirect("app_run:list_runs", instance_id=instance_id)


def view_run_result(request, instance_id, run_id):
    """
    View the result of a run under an app instance when request is GET
    """
    app_run = AppRun.objects.get(id=run_id)

    nb_str = json.dumps(app_run.output_artifacts)
    nb = nbformat.reads(nb_str, as_version=4)

    # render the notebook in html format
    htmp_exporter = nbconvert.HTMLExporter()
    html, _ = htmp_exporter.from_notebook_node(nb)

    return HttpResponse(html)
