from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("apps/", include("apps.trac_app.urls")),
    path("data_gateway/", include("apps.data_gateway.urls")),
    path("app_run/", include("apps.app_run.urls")),
]
