from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles):
    """
    Decorator for views that checks if the user has one of the allowed roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Superuser always bypasses check
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # Redirect to dashboard with a warning message (handled by messaging usually, 
            # but for now just redirecting or raising 403 if stricter)
            # Using redirect as per original code behavior
            return redirect('dashboard')
            
        return _wrapped_view
    return decorator
