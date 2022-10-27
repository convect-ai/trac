from django import forms

from .models import DataSet


class DatasetForm(forms.ModelForm):
    class Meta:
        model = DataSet
        fields = ["name", "description", "backend"]
