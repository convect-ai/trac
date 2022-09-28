from django.urls import path

from .views import *

app_name = "data_gateway"

urlpatterns = [
    path("<int:instance_id>/datasets/", list_datasets, name="list_datasets"),
    path("<int:instance_id>/datasets/create/", create_dataset, name="create_dataset"),
    path(
        "<int:instance_id>/datasets/<int:dataset_id>/update/",
        update_dataset,
        name="update_dataset",
    ),
    path(
        "<int:instance_id>/datasets/<int:dataset_id>/delete/",
        delete_dataset,
        name="delete_dataset",
    ),
    path(
        "<int:instance_id>/datasets/<int:dataset_id>/manage/",
        dataset_input_view,
        name="view_input",
    ),
    path(
        "<int:instance_id>/datasets/<int:dataset_id>/save/",
        dataset_input_view_save,
        name="save_data",
    ),
]
