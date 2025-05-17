"""
from users.permissions import (
    IsAdmin, IsAdminOrReadOnly, IsAuthorModeratorAdminOrReadOnly
)
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly

Выбирайте нужный класс:

Только для администратора:
    permission_classes = [IsAdmin]

Чтение — всем, изменения — только админу:
    permission_classes = [IsAdminOrReadOnly]

Чтение — всем. Изменение — автору, модератору или админу:
    permission_classes = [IsAuthorModeratorAdminOrReadOnly]

Открытый доступ для анонимов:
    permission_classes = [AllowAny]


- Всегда прописывать permission_classes явно
- Если используется проверка автора — у модели должно быть поле `author`
- Если не указать permission_classes — сработает DEFAULT_PERMISSION_CLASSES из settings.py:
    'rest_framework.permissions.IsAuthenticatedOrReadOnly'
"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Доступ только для админов (роль 'admin' или superuser).
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_admin
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Чтение — всем, изменения — только админам.
    """
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (
                request.user.is_authenticated
                and request.user.is_admin
            )
        )


class IsAuthorModeratorAdminOrReadOnly(permissions.BasePermission):
    """
    Чтение — всем.
    Изменение/удаление — автору объекта, модератору или админу.
    """
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.is_moderator
            or request.user.is_admin
        )
