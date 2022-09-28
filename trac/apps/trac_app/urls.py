from django.urls import path

from .views import *

app_name = "trac_app"
urlpatterns = [
    path("", list_apps, name="list_apps"),
    path("create/", create_app, name="create_app"),
    path("update/<int:app_def_id>/", update_app, name="update_app"),
    path("delete/<int:app_def_id>/", delete_app, name="delete_app"),
    path("<int:app_def_id>/instances/", list_app_instances, name="list_app_instances"),
    path(
        "<int:app_def_id>/instances/create/",
        create_app_instance,
        name="create_app_instance",
    ),
    path(
        "instances/update/<int:app_id>/",
        update_app_instance,
        name="update_app_instance",
    ),
    path(
        "instances/delete/<int:app_id>/",
        delete_app_instance,
        name="delete_app_instance",
    ),
]
