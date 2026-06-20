from rest_framework import serializers

from .models import Bureau, Direction, Function, Grade, Service, SubDirection


class DirectionSerializer(serializers.ModelSerializer):
    sub_directions_count = serializers.SerializerMethodField()

    class Meta:
        model = Direction
        fields = [
            "id", "name", "code", "description",
            "is_active", "ordering",
            "sub_directions_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "sub_directions_count"]

    def get_sub_directions_count(self, obj):
        return obj.sub_directions.filter(is_deleted=False, is_active=True).count()


class SubDirectionSerializer(serializers.ModelSerializer):
    direction_name = serializers.CharField(source="direction.name", read_only=True)
    services_count = serializers.SerializerMethodField()

    class Meta:
        model = SubDirection
        fields = [
            "id", "direction", "direction_name",
            "name", "code", "description",
            "is_active", "ordering",
            "services_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "direction_name", "services_count"]

    def get_services_count(self, obj):
        return obj.services.filter(is_deleted=False, is_active=True).count()


class ServiceSerializer(serializers.ModelSerializer):
    sub_direction_name = serializers.CharField(source="sub_direction.name", read_only=True)
    direction_id = serializers.UUIDField(source="sub_direction.direction_id", read_only=True)
    bureaux_count = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id", "sub_direction", "sub_direction_name", "direction_id",
            "name", "code", "description",
            "is_active", "ordering",
            "bureaux_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "sub_direction_name", "direction_id", "bureaux_count"]

    def get_bureaux_count(self, obj):
        return obj.bureaux.filter(is_deleted=False, is_active=True).count()


class BureauSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    sub_direction_id = serializers.UUIDField(source="service.sub_direction_id", read_only=True)
    direction_id = serializers.UUIDField(source="service.sub_direction.direction_id", read_only=True)

    class Meta:
        model = Bureau
        fields = [
            "id", "service", "service_name",
            "sub_direction_id", "direction_id",
            "name", "code", "description",
            "is_active", "ordering",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "service_name", "sub_direction_id", "direction_id"]


class FunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Function
        fields = [
            "id", "name", "description",
            "is_active", "ordering",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = [
            "id", "name", "level", "description",
            "is_active", "ordering",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
