import hashlib

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

    schema = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # reoder the keys and values in the schema in alphabetical order recursively
        self.schema = self._sort_dict(self.schema)
        super().save(*args, **kwargs)

    def _sort_dict(self, d):
        if isinstance(d, dict):
            return {k: self._sort_dict(v) for k, v in sorted(d.items())}
        elif isinstance(d, list):
            return [self._sort_dict(x) for x in d]
        else:
            return d

    def schema_hash(self):
        """
        Hash value of the schema
        So that we can compare the schema of two datasets
        """
        return hashlib.sha256(str(self.schema).encode("utf-8")).hexdigest()


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
