"""RBAC permissions package — strategy-based authorization."""

from rest_api.app.services.permissions.context import PermissionContext
from rest_api.app.services.permissions.strategies import Action

__all__ = ["Action", "PermissionContext"]
