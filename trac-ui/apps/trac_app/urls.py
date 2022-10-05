from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    AppDefinitionViewSet,
    AppInstanceListCreateAPIView,
    AppInstanceRetrieveUpdateDestroyAPIView,
    dashboard,
)

app_name = "trac_app"

router = SimpleRouter()
router.register(r"api/apps", AppDefinitionViewSet, basename="app")

urlpatterns = [
    path("instances/<int:instance_id>/dashboard/", dashboard, name="dashboard"),
    path(
        "api/apps/<int:app_def_id>/instances/",
        AppInstanceListCreateAPIView.as_view(),
        name="app_instance_list",
    ),
    path(
        "api/apps/<int:app_def_id>/instances/<int:app_inst_id>",
        AppInstanceRetrieveUpdateDestroyAPIView.as_view(),
        name="app_instance_detail",
    ),
]

urlpatterns += router.urls
