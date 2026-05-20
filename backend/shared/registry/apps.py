from django.apps import AppConfig


class RegistryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shared.registry"
    verbose_name = "Moteur d'enregistrement"
