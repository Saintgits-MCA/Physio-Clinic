from django.http import HttpResponseForbidden
from functools import wraps
from django.shortcuts import redirect
from .utils.permissions import has_menu_permission

def require_menu_permission(permission_type='view'):
    """
    Decorator to check if user has permission to access a view
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            staff_id = request.session.get('staff_id')
            
            if not staff_id:
                return redirect('login')
                
            # Get the current URL path
            current_path = request.path
            
            # Check permission
            if not has_menu_permission(staff_id, current_path, permission_type):
                return HttpResponseForbidden("You don't have permission to access this page")
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

