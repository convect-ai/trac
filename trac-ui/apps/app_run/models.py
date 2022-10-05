from apps.data_gateway.models import DataSet
from apps.trac_app.models import AppInstance
from django.db import models


class AppRun(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    app = models.ForeignKey(AppInstance, on_delete=models.CASCADE, related_name="runs")
    dataset = models.ForeignKey(DataSet, on_delete=models.CASCADE, related_name="runs")
    parameters = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=100,
        choices=[
            ("PENDING", "PENDING"),
            ("RUNNING", "RUNNING"),
            ("COMPLETED", "COMPLETED"),
            ("FAILED", "FAILED"),
        ],
        default="PENDING",
    )
    output_artifacts = models.JSONField(null=True, blank=True)
    logs = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
