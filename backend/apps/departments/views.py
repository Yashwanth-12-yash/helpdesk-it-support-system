from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import DepartmentPermission
from .selectors import get_departments_queryset
from .serializers import DepartmentSerializer, DepartmentWriteSerializer
from .services import create_department, update_department


class DepartmentViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_classes = [IsAuthenticated, DepartmentPermission]
    filterset_fields = ["is_active", "manager"]
    search_fields = ["name", "code", "description"]
    ordering_fields = ["name", "code", "created_at"]

    def get_queryset(self):
        return get_departments_queryset(requesting_user=self.request.user)

    def get_serializer_class(self):
        if self.action in {"create", "partial_update", "update"}:
            return DepartmentWriteSerializer
        return DepartmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dept = create_department(created_by=request.user, **serializer.validated_data)
        return Response(DepartmentSerializer(dept).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        dept = self.get_object()
        serializer = self.get_serializer(dept, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = update_department(department=dept, updated_by=request.user, **serializer.validated_data)
        return Response(DepartmentSerializer(updated).data)
