import hashlib
import json

from apps.trac_app.models import AppInstance
from django.db import models
from trac.schema.task import FileDef


# custom json decoder for the schema type
# schema takes the form {"input_schema": List[FileDef], "output_schema": List[FileDef]}
class FileDefListDecoder(json.JSONDecoder):
    def decode(self, s):
        d = super().decode(s)
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, list):
                    d[k] = [FileDef(**x) for x in v]
        return d


# custom json encoder for the schema type
# schema takes the form {"input_schema": List[FileDef], "output_schema": List[FileDef]}
class FileDefListEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, FileDef):
            return o.dict()
        else:
            return super().default(o)


class DataSet(models.Model):
    """
    A dataset = a workbook in excel
    """

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    app = models.ForeignKey(
        AppInstance, on_delete=models.CASCADE, related_name="datasets"
    )

    schema = models.JSONField(
        blank=True, null=True, decoder=FileDefListDecoder, encoder=FileDefListEncoder
    )

    initialized = models.BooleanField(default=False)
    url = models.CharField(max_length=1000, blank=True, null=True)
    backend = models.CharField(
        max_length=100,
        choices=[
            ("excel", "Excel"),
            ("db", "Database"),
            ("gsheet", "Google Sheet"),
        ],
        default="db",
    )

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
