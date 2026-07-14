# context_processors.py
from django.shortcuts import redirect
from .models import RoleAssignment, MenuPermission

def staff_menu_permissions(request):
    staff_id = request.session.get("staff_id")
    if not staff_id:
        return {}

    # Get active role assignment(s) for this staff
    role_assignments = RoleAssignment.objects.filter(staff_id=staff_id, status=True)
    if not role_assignments.exists():
        return {}

    role_ids = role_assignments.values_list("role_id", flat=True)

    # Fetch menu permissions for these roles
    perms = (
        MenuPermission.objects.filter(role_id__in=role_ids, can_view=True)
        .select_related("menu")
    )
    allowed_urls = [perm.menu.url for perm in perms]
    # Organize into categories
    allowed_menus = {}
    for perm in perms:
        category = perm.menu.category  # assuming `category` field exists in Menu
        if category not in allowed_menus:
            allowed_menus[category] = []
        allowed_menus[category].append({
            "name": perm.menu.name,
            "url": perm.menu.url,   # menu’s url from DB
            "icon": getattr(perm.menu, "icon", None),  # if you have an icon field
        })
    return {"allowed_menus": allowed_menus, "allowed_urls": allowed_urls}
