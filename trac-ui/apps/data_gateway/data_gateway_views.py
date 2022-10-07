"""
API views for managing resource under a dataset
"""

import re

from django.http import Http404
from rest_framework import generics, mixins, serializers

from .models import DataSet, Resource


def convert_jsonschema_to_serializers(resource_schema):
    """
    Convert a JSON schema to a serializer
    """
    # construct a serializer class, which is a subclass of serializers.Serializer
    # each field of the serializer corresponds to a property of the resource_schema
    class ResourceSerializer(serializers.Serializer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            field_name_mapping = {}

            for field_name, field_schema in resource_schema["properties"].items():
                # sanitize the field_name, by replacing all non-alphanumeric characters with _
                field_name_sanitized = re.sub(r"\W+", "_", field_name)
                field_name_mapping[field_name_sanitized] = field_name

                # map the field_schema to a serializer field
                field_type = field_schema["type"]
                if field_type == "string":
                    serializer_field = serializers.CharField()
                elif field_type == "integer":
                    serializer_field = serializers.IntegerField()
                elif field_type == "number":
                    serializer_field = serializers.FloatField()
                elif field_type == "boolean":
                    serializer_field = serializers.BooleanField()
                elif field_type == "array":
                    serializer_field = serializers.ListField()
                elif field_type == "object":
                    serializer_field = serializers.DictField()
                else:
                    raise ValueError("Unsupported field type: {}".format(field_type))

                self.fields[field_name_sanitized] = serializer_field

            # add an id field
            self.fields["id"] = serializers.IntegerField(required=False)

            self.field_name_mapping = field_name_mapping

        # def to_representation(self, instance):
        #     """
        #     Convert the instance to a dict, where the keys are the field names
        #     """
        #     res = super().to_representation(instance)
        #     return {
        #         field_name_sanitized: res[field_name]
        #         for field_name_sanitized, field_name in self.field_name_mapping.items()
        #     }

        def to_internal_value(self, data):
            """
            Convert the data to a dict, where the keys are the field names
            """
            res = super().to_internal_value(data)
            return {
                field_name: res[field_name_sanitized]
                for field_name_sanitized, field_name in self.field_name_mapping.items()
            }

    return ResourceSerializer


class ResourceListCreateView(generics.ListCreateAPIView):
    """
    List and create resources for a dataset
    """

    def get_queryset(self):
        dataset_id = self.kwargs.get("dataset_id")
        dataset = DataSet.objects.get(id=dataset_id)
        resource_type = self.kwargs.get("resource_type")

        # check if dataset schema contains the resource_type
        # if not return a 404 error
        schema = dataset.schema["input_schema"]
        resource_schema = None
        for resource_schema in schema:
            if resource_schema["title"] == resource_type:
                break
        else:
            raise Http404(f"Resource type {resource_type} not found")

        resources = Resource.objects.filter(
            dataset=dataset, resource_type=resource_type
        ).all()
        # sanitize the resource values
        result = []
        for resource in resources:
            resource_id = resource.id
            value = resource.value
            new_value = {}
            for field_name, field_value in value.items():
                # replace all non-alphanumeric characters with _
                field_name_sanitized = re.sub(r"\W+", "_", field_name)
                new_value[field_name_sanitized] = field_value
            result.append({"id": resource_id, **new_value})
        return result

    def get_serializer_class(self):
        """
        Return a dynamic serializer class based on the resource_type
        """
        resource_type = self.kwargs.get("resource_type")

        # schema of the resource_type
        dataset_id = self.kwargs.get("dataset_id")
        dataset = DataSet.objects.get(id=dataset_id)
        schema = dataset.schema["input_schema"]
        resource_schema = None
        for resource_schema in schema:
            if resource_schema["title"] == resource_type:
                break

        return convert_jsonschema_to_serializers(resource_schema)

    def perform_create(self, serializer):
        dataset_id = self.kwargs.get("dataset_id")
        dataset = DataSet.objects.get(id=dataset_id)
        resource_type = self.kwargs.get("resource_type")

        value = serializer.validated_data
        resource = Resource(dataset=dataset, resource_type=resource_type, value=value)
        resource.save()


class ResourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update and delete a resource
    """

    lookup_field = "resource_id"

    def get_queryset(self):
        dataset_id = self.kwargs.get("dataset_id")
        dataset = DataSet.objects.get(id=dataset_id)
        resource_type = self.kwargs.get("resource_type")

        # check if dataset schema contains the resource_type
        # if not return a 404 error
        schema = dataset.schema["input_schema"]
        resource_schema = None
        for resource_schema in schema:
            if resource_schema["title"] == resource_type:
                break
        else:
            raise Http404(f"Resource type {resource_type} not found")

        resources = Resource.objects.filter(
            dataset=dataset, resource_type=resource_type
        ).all()
        return resources

    def get_object(self):
        resources = self.get_queryset()
        resource_id = self.kwargs.get("resource_id")
        resource = resources.get(id=resource_id)
        # sanitize the resource values
        resource_id = resource.id
        value = resource.value
        new_value = {}
        for field_name, field_value in value.items():
            # replace all non-alphanumeric characters with _
            field_name_sanitized = re.sub(r"\W+", "_", field_name)
            new_value[field_name_sanitized] = field_value

        return {"id": resource_id, **new_value}

    def get_serializer_class(self):
        """
        Return a dynamic serializer class based on the resource_type
        """
        resource_type = self.kwargs.get("resource_type")

        # schema of the resource_type
        dataset_id = self.kwargs.get("dataset_id")
        dataset = DataSet.objects.get(id=dataset_id)
        schema = dataset.schema["input_schema"]
        resource_schema = None
        for resource_schema in schema:
            if resource_schema["title"] == resource_type:
                break

        return convert_jsonschema_to_serializers(resource_schema)

    def perform_update(self, serializer):
        value = serializer.validated_data
        resource_id = self.kwargs.get(self.lookup_field)
        resource = Resource.objects.get(id=resource_id)
        resource.value = value
        resource.save()

    def perform_destroy(self, instance):
        resource_id = self.kwargs.get(self.lookup_field)
        resource = Resource.objects.get(id=resource_id)
        resource.delete()
