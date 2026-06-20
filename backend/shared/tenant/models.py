import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name=_("Nom"))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_("Slug"))
    domain = models.CharField(
        max_length=200, blank=True, verbose_name=_("Domaine"),
        help_text=_("Domaine personnalisé (optionnel)"),
    )
    logo = models.ImageField(upload_to="tenants/", null=True, blank=True, verbose_name=_("Logo"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    max_users = models.PositiveIntegerField(default=100, verbose_name=_("Nombre max d'utilisateurs"))
    config = models.JSONField(default=dict, blank=True, verbose_name=_("Configuration"))
    features = models.JSONField(
        default=dict, blank=True, verbose_name=_("Fonctionnalités"),
        help_text=_("Feature flags au format JSON"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tenant")
        verbose_name_plural = _("Tenants")
        ordering = ["name"]

    def __str__(self):
        return self.name
