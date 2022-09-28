from django import forms
from runtime.local import RuntimeFactory

from .models import AppDefinition, AppInstance


class AppDefinitionForm(forms.ModelForm):
    class Meta:
        model = AppDefinition
        fields = "__all__"

    def clean(self):
        image_name = self.cleaned_data["image_name"]
        image_tag = self.cleaned_data["image_tag"]

        runtime = RuntimeFactory.get_runtime()
        try:
            runtime.validate_image_exists(image_name, image_tag)
        except Exception as e:
            raise forms.ValidationError(e)


class AppInstanceForm(forms.ModelForm):
    class Meta:
        model = AppInstance
        fields = [
            "name",
            "description",
        ]
