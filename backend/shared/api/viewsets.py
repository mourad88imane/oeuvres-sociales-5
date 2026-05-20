"""
============================================================
API VIEWSETS — Classes de base pour tous les ViewSets
============================================================
Utilisation :
    class MyViewSet(GenericModelViewSet):
        serializer_class = MySerializer
        permission_classes = [IsAuthenticated]
"""
from rest_framework import viewsets, mixins
from core.pagination import StandardResultsSetPagination
from .responses import success_response


class GenericModelViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet CRUD complet avec pagination standard.
    
    - Pagination : StandardResultsSetPagination (25/page)
    - Réponses formatées automatiquement
    """
    pagination_class = StandardResultsSetPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(serializer.data, status_code=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(message="Ressource supprimée")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def get_paginated_response(self, data):
        from .responses import paginated_response
        return paginated_response(data, self)
