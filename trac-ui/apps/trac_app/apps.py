from django.apps import AppConfig


class TracAppConfig(AppConfig):
    """
    App to manage publishing of trac apps
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trac_app"
