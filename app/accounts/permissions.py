from functools import wraps

from django.shortcuts import render

from .models import UserRestaurant


SUPERADMIN = UserRestaurant.ROLE_SUPERADMIN
ADMIN = UserRestaurant.ROLE_ADMIN
CAJERO = UserRestaurant.ROLE_CAJERO
COCINA = UserRestaurant.ROLE_COCINA
MESERO = UserRestaurant.ROLE_MESERO

MODULE_ROLE_MAP = {
    'dashboard': {SUPERADMIN, ADMIN},
    'pos': {SUPERADMIN, ADMIN, CAJERO, MESERO},
    'kitchen': {SUPERADMIN, ADMIN, COCINA},
    'tables': {SUPERADMIN, ADMIN, MESERO},
    'orders': {SUPERADMIN, ADMIN, CAJERO, MESERO},
    'payments': {SUPERADMIN, ADMIN, CAJERO},
    'reports': {SUPERADMIN, ADMIN},
    'products': {SUPERADMIN, ADMIN, CAJERO},
}


def get_user_role(user):
    if not user.is_authenticated:
        return None

    if user.is_superuser:
        return SUPERADMIN

    profile = getattr(user, 'restaurant_profile', None)
    return profile.role if profile else None


def user_is_superadmin(user):
    return get_user_role(user) == SUPERADMIN


def user_has_role(user, roles):
    if isinstance(roles, str):
        roles = {roles}

    return get_user_role(user) in roles


def user_can_access_module(user, module):
    return user_has_role(user, MODULE_ROLE_MAP.get(module, set()))


def is_saas_superadmin(user):
    return user_is_superadmin(user)


def has_role(user, roles):
    return user_has_role(user, roles)


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not user_has_role(request.user, set(roles)):
                return render(request, 'auth/403.html', status=403)

            if not user_is_superadmin(request.user) and not getattr(request, 'restaurant', None):
                return render(request, 'auth/403.html', {
                    'message': 'Tu usuario no tiene un restaurante asignado.',
                }, status=403)

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def tenant_filter(request, field='restaurant'):
    if user_is_superadmin(request.user) and not getattr(request, 'restaurant', None):
        return {}

    return {field: request.restaurant}


def tenant_order_filter(request, field='order__restaurant'):
    if user_is_superadmin(request.user) and not getattr(request, 'restaurant', None):
        return {}

    return {field: request.restaurant}
