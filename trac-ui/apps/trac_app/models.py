from functools import cached_property, lru_cache

from django.db import models

from .docker_utils import DockerUtils


class AppDefinition(models.Model):

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    image_name = models.CharField(max_length=100)
    image_tag = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    @property
    def default_task(self):
        return self.tasks[0]

    @cached_property
    def spec(self):
        """
        Return the spec of the app
        """
        return DockerUtils.spec(self.image_name, self.image_tag)

    @cached_property
    def tasks(self):
        """
        Return the tasks of the app
        """
        return DockerUtils.tasks(self.image_name, self.image_tag)

    @lru_cache
    def task_spec(self, task_name):
        """
        Return the spec of a task
        """

        return DockerUtils.spec(self.image_name, self.image_tag, task_name=task_name)

    @lru_cache
    def input_schema(self, task_name=None):
        """
        Return the input schema of the app
        """
        if not task_name:
            task_name = self.default_task
        return DockerUtils.input_schema(
            self.image_name, self.image_tag, task_name=task_name
        )

    @lru_cache
    def output_schema(self, task_name=None):
        """
        Return the output schema of the app
        """

        if not task_name:
            task_name = self.default_task
        return DockerUtils.output_schema(
            self.image_name, self.image_tag, task_name=task_name
        )

    @lru_cache
    def parameter_schema(self, task_name=None):
        """
        Return the parameter schema of the app
        """
        if not task_name:
            task_name = self.default_task
        return DockerUtils.parameter_schema(
            self.image_name, self.image_tag, task_name=task_name
        )


class AppInstance(models.Model):

    app = models.ForeignKey(AppDefinition, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.name
