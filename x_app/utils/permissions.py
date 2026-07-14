from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from x_app.models import RoleAssignment, MenuPermission

def user_has_permission(user, menu_name, action):
    try:
        role_assignment = RoleAssignment.objects.get(staff=user, status=True)
        role = role_assignment.role
    except RoleAssignment.DoesNotExist:
        return False

    # ✅ Admin override: Admin role sees everything
    if role.name.lower() == "admin":
        return True

    try:
        menu_perm = MenuPermission.objects.get(role=role, menu__name=menu_name)
        return getattr(menu_perm, f"can_{action}", False)
    except MenuPermission.DoesNotExist:
        return False
    
def user_is_admin(user):
    try:
        assignment = RoleAssignment.objects.select_related("role").get(staff=user)
        return assignment.role.name.lower() == "admin" and assignment.status == 1
    except RoleAssignment.DoesNotExist:
        return False
    
def get_user_permissions(user):
    try:
        role_assignment = RoleAssignment.objects.get(staff=user)
        role = role_assignment.role
        permissions = MenuPermission.objects.filter(role=role)
        return {perm.menu.name: {
                    'view': perm.can_view,
                    'add': perm.can_add,
                    'edit': perm.can_edit,
                    'delete': perm.can_delete
                } for perm in permissions}
    except RoleAssignment.DoesNotExist:
        return {}