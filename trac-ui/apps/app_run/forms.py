from typing import List

from apps.data_gateway.models import DataSet
from django import forms
from trac.schema.task import ParameterDef


def create_form_from_parameter_schema(
    parameter_schema: List[ParameterDef], instance_id
):
    # paramter_schema is a jsonschema
    # create a dynamic form based on the parameter_schema
    class AppRunForm(forms.Form):

        name = forms.CharField(max_length=100)
        description = forms.CharField(max_length=100)
        dataset = forms.ModelChoiceField(
            queryset=DataSet.objects.filter(app__pk=instance_id).all(),
        )

        def __init__(self, *args, **kwargs):
            super(AppRunForm, self).__init__(*args, **kwargs)
            properties = {}
            for param_def in parameter_schema:
                param_name = param_def.name
                param_type = param_def.type
                default = param_def.default
                description = param_def.description

                properties[param_name] = {
                    "type": param_type,
                    "default": default,
                    "description": description,
                }

            for field, value in properties.items():
                # get the field type
                field_type = value["type"]
                default_value = value.get("default", None)
                # convert the field type to a django form field
                if field_type == "string":
                    self.fields[field] = forms.CharField()
                elif field_type == "integer":
                    self.fields[field] = forms.IntegerField()
                elif field_type == "number":
                    self.fields[field] = forms.FloatField()
                elif field_type == "boolean":
                    self.fields[field] = forms.BooleanField(required=False)
                else:
                    raise Exception("Unsupported field type: {}".format(field_type))
                if default_value:
                    self.fields[field].initial = default_value
                    # set the field as not required
                    self.fields[field].required = False

        def clean(self):
            cleaned_data = super(AppRunForm, self).clean()
            # remove the fields that are in the parameter_schema
            parameters = {}
            param_names = [param_def.name for param_def in parameter_schema]
            for field in param_names:
                value = cleaned_data.pop(field)
                parameters[field] = value
            cleaned_data["parameters"] = parameters
            return cleaned_data

    return AppRunForm
