from rest_framework.permissions import BasePermission

METHODS = ('POST', 'HEAD', 'OPTIONS')


class WriteOnlyPermission(BasePermission):
    """
    The request is a write-only request.
    """

    def has_permission(self, request, view):
        return request.method in METHODS
