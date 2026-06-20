from django.contrib import admin

from .models import Bureau, Direction, Function, Grade, Service, SubDirection


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "ordering"]
    list_filter = ["is_active"]
    search_fields = ["code", "name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SubDirection)
class SubDirectionAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "direction", "is_active", "ordering"]
    list_filter = ["is_active", "direction"]
    search_fields = ["code", "name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "sub_direction", "is_active", "ordering"]
    list_filter = ["is_active", "sub_direction__direction"]
    search_fields = ["code", "name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Bureau)
class BureauAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "service", "is_active", "ordering"]
    list_filter = ["is_active", "service__sub_direction__direction"]
    search_fields = ["code", "name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "ordering"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ["name", "level", "is_active", "ordering"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
