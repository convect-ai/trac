from django.urls import path

from .views import *

app_name = "app_run"

urlpatterns = [
    path("<int:instance_id>/runs/create/", create_run, name="create_run"),
    path("<int:instance_id>/runs/<int:run_id>/update/", update_run, name="update_run"),
    path("<int:instance_id>/runs/<int:run_id>/delete/", delete_run, name="delete_run"),
    path(
        "<int:instance_id>/runs/<int:run_id>/view/", view_run_result, name="view_result"
    ),
    path("<int:instance_id>/runs/<int:run_id>/logs/", view_run_logs, name="view_logs"),
]
