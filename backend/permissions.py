from rest_framework.permissions import BasePermission


class IsSupplier(BasePermission):
    """Разрешает доступ только поставщикам."""

    message = "Доступ разрешён только поставщикам."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_supplier
