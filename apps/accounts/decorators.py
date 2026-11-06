from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def access_required(permission_attr):
    """Batasi view berdasarkan properti di model User.

    Contoh: @access_required("can_manage_inbox")
    """

    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not getattr(request.user, permission_attr, False):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapper

    return decorator