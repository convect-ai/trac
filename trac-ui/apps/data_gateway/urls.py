from django.urls import path

from .data_gateway_views import *
from .views import *

app_name = "data_gateway"

urlpatterns = [
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
    path(
        "datasets/<int:dataset_id>/spec.json", dataset_api_spec, name="dataset_api_spec"
    ),
    path(
        "datasets/<int:dataset_id>/swagger-ui",
        dataset_api_swagger_ui,
        name="dataset_swagger_ui",
    ),
    path(
        "datasets/<int:dataset_id>/api/<str:resource_type>/",
        ResourceListCreateView.as_view(),
        name="resource_list_create",
    ),
    path(
        "datasets/<int:dataset_id>/api/<str:resource_type>/<int:resource_id>/",
        ResourceDetailView.as_view(),
        name="resource_retrieve_update_destroy",
    ),
]
