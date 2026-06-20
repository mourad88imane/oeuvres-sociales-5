from django.db import models

from core.models import BaseModel


class Direction(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Direction")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    ordering = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta(BaseModel.Meta):
        verbose_name = "Direction"
        verbose_name_plural = "Directions"
        ordering = ["ordering", "name"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class SubDirection(BaseModel):
    direction = models.ForeignKey(
        Direction, on_delete=models.CASCADE,
        related_name="sub_directions", verbose_name="Direction",
    )
    name = models.CharField(max_length=255, verbose_name="Sous-Direction")
    code = models.CharField(max_length=20, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    ordering = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta(BaseModel.Meta):
        verbose_name = "Sous-Direction"
        verbose_name_plural = "Sous-Directions"
        ordering = ["ordering", "name"]
        unique_together = [["direction", "code"]]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Service(BaseModel):
    sub_direction = models.ForeignKey(
        SubDirection, on_delete=models.CASCADE,
        related_name="services", verbose_name="Sous-Direction",
    )
    name = models.CharField(max_length=255, verbose_name="Service")
    code = models.CharField(max_length=20, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    ordering = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta(BaseModel.Meta):
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ["ordering", "name"]
        unique_together = [["sub_direction", "code"]]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Bureau(BaseModel):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE,
        related_name="bureaux", verbose_name="Service",
    )
    name = models.CharField(max_length=255, verbose_name="Bureau")
    code = models.CharField(max_length=20, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    ordering = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta(BaseModel.Meta):
        verbose_name = "Bureau"
        verbose_name_plural = "Bureaux"
        ordering = ["ordering", "name"]
        unique_together = [["service", "code"]]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Function(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name="Fonction")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    ordering = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta(BaseModel.Meta):
        verbose_name = "Fonction"
        verbose_name_plural = "Fonctions"
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name


class Grade(BaseModel):
    name = models.CharField(max_length=255, verbose_name="Grade")
    level = models.PositiveIntegerField(verbose_name="Niveau")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    ordering = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta(BaseModel.Meta):
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        ordering = ["level", "name"]
        unique_together = [["name", "level"]]

    def __str__(self):
        return f"{self.name} (Niv. {self.level})"
