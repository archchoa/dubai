from rest_framework import permissions


class IsAuthenticatedAndActive(permissions.IsAuthenticated):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        _has_permission = super(IsAuthenticatedAndActive, self) \
                                 .has_permission(request, view)
        return _has_permission and request.user.is_active
