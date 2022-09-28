from django.shortcuts import redirect, render

from .forms import AppDefinitionForm, AppInstanceForm
from .models import AppDefinition, AppInstance


def list_apps(request):
    """
    Show a list of registered apps when request is GET
    """
    app_defs = AppDefinition.objects.all()
    return render(request, "trac_app/list_apps.html", {"app_defs": app_defs})


def create_app(request):
    """
    Create a AppDefinition when request
    """
    if request.method == "POST":
        form = AppDefinitionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("trac_app:list_apps")
    else:
        form = AppDefinitionForm()
    return render(request, "trac_app/create_app.html", {"form": form})


def update_app(request, app_def_id):
    """
    Update a AppDefinition when request is PUT
    """
    app_def = AppDefinition.objects.get(id=app_def_id)
    if request.method == "POST":
        form = AppDefinitionForm(request.POST, instance=app_def)
        if form.is_valid():
            form.save()
            return redirect("trac_app:list_apps")
    else:
        form = AppDefinitionForm(instance=app_def)
    return render(request, "trac_app/creqte_app.html", {"form": form})


def delete_app(request, app_def_id):
    """
    Delete a AppDefinition when request is DELETE
    """
    if request.method == "POST":
        app_def = AppDefinition.objects.get(id=app_def_id)
        app_def.delete()
        return redirect("trac_app:list_apps")


def list_app_instances(request, app_def_id):
    """
    Show a list of app instances when request is GET
    """
    apps = AppInstance.objects.filter(app__pk=app_def_id).all()
    return render(
        request,
        "trac_app/list_app_instances.html",
        {"apps": apps, "app_def_id": app_def_id},
    )


def create_app_instance(request, app_def_id):
    """
    Create a AppInstance when request is POST
    """
    if request.method == "POST":
        form = AppInstanceForm(request.POST)
        if form.is_valid():
            # set the app definition id
            app = form.save(commit=False)
            app.app_id = app_def_id
            app.save()
            return redirect("trac_app:list_app_instances", app_def_id=app_def_id)
    else:
        form = AppInstanceForm()
    return render(
        request,
        "trac_app/create_app_instance.html",
        {"form": form, "app_def_id": app_def_id},
    )


def update_app_instance(request, app_id):
    """
    Update a AppInstance when request is PUT
    """
    app = AppInstance.objects.get(id=app_id)
    if request.method == "POST":
        form = AppInstanceForm(request.POST, instance=app)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.app_id = app.app_id
            instance.save()
            return redirect("trac_app:list_app_instances", app_def_id=app.app_id)
    else:
        form = AppInstanceForm(instance=app)
    return render(
        request,
        "trac_app/create_app_instance.html",
        {"form": form, "app_def_id": app.app_id},
    )


def delete_app_instance(request, app_id):
    """
    Delete a AppInstance when request is DELETE
    """
    if request.method == "POST":
        app = AppInstance.objects.get(id=app_id)
        app.delete()
        return redirect("trac_app:list_app_instances", app_def_id=app.app_id)
