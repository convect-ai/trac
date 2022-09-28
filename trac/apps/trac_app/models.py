from unicodedata import name

from django.db import models


class AppDefinition(models.Model):

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    image_name = models.CharField(max_length=100)
    image_tag = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class AppInstance(models.Model):

    app = models.ForeignKey(AppDefinition, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.name
