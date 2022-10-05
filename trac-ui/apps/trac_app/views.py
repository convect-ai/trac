from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.serializers import ModelSerializer, ValidationError
from rest_framework.viewsets import ModelViewSet
from runtime.local import RuntimeFactory

from .models import AppDefinition, AppInstance


class AppDefinitionSerializer(ModelSerializer):
    class Meta:
        model = AppDefinition
        fields = "__all__"

    def validate(self, attrs):
        image_name = attrs["image_name"]
        image_tag = attrs["image_tag"]

        runtime = RuntimeFactory.get_runtime()
        try:
            runtime.validate_image_exists(image_name, image_tag)
        except Exception as e:
            raise ValidationError(e)

        return attrs


class AppInstanceSerializer(ModelSerializer):
    class Meta:
        model = AppInstance
        fields = [
            "id",
            "name",
            "description",
        ]


class AppDefinitionViewSet(ModelViewSet):
    queryset = AppDefinition.objects.all().order_by("pk")
    serializer_class = AppDefinitionSerializer


# /api/apps/<app_def_id>/instances
class AppInstanceListCreateAPIView(ListCreateAPIView):
    serializer_class = AppInstanceSerializer

    def get_queryset(self):
        app_def_id = self.kwargs["app_def_id"]
        return AppInstance.objects.filter(app__pk=app_def_id).all()

    def perform_create(self, serializer):
        app_def_id = self.kwargs["app_def_id"]
        app_def = AppDefinition.objects.get(id=app_def_id)
        serializer.save(app=app_def)


# /api/apps/<app_def_id>/instances/<app_inst_id>
class AppInstanceRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = AppInstanceSerializer
    queryset = AppInstance.objects.all()

    def get_object(self):
        app_def_id = self.kwargs["app_def_id"]
        app_inst_id = self.kwargs["app_inst_id"]
        return self.get_queryset().filter(app__pk=app_def_id, id=app_inst_id).first()


# /instances/<instance_id>/dashboard
def dashboard(request, instance_id):
    app = AppInstance.objects.get(id=instance_id)

    # all runs belong to this instance
    runs = app.runs.all()

    datasets = app.datasets.all()

    context = {
        "runs": runs,
        "datasets": datasets,
        "instance_id": instance_id,
    }

    return render(
        request,
        "trac_app/manage_instance.html",
        context,
    )
