from apps.trac_app.models import AppInstance
from django.db import models


class DataSet(models.Model):
    """
    A dataset = a workbook in excel
    """

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    app = models.ForeignKey(
        AppInstance, on_delete=models.CASCADE, related_name="datasets"
    )

    def __str__(self):
        return self.name


class Resource(models.Model):
    """
    A resource is a sheet in a workbook
    """

    dataset = models.ForeignKey(
        DataSet, on_delete=models.CASCADE, related_name="resources"
    )
    resource_type = models.CharField(max_length=100)
    value = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name
