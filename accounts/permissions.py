from rest_framework.permissions import BasePermission
from .models import CustomUser


class IsAdmin(BasePermission):
    """Allow access only to admin users."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.ROLE_ADMIN
        )


class IsTeacher(BasePermission):
    """Allow access only to teacher users."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.ROLE_TEACHER
        )


class IsStudent(BasePermission):
    """Allow access only to student users."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.ROLE_STUDENT
        )


class IsAdminOrTeacher(BasePermission):
    """Allow access to admins or teachers."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in (CustomUser.ROLE_ADMIN, CustomUser.ROLE_TEACHER)
        )


class IsAdminOrReadOwn(BasePermission):
    """Admin can do anything; others can only read their own data."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == CustomUser.ROLE_ADMIN:
            return True
        return obj == request.user
