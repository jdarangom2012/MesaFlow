from django.shortcuts import render

from .permissions import MODULE_ROLE_MAP, get_user_role, user_can_access_module, user_is_superadmin


class RestaurantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.restaurant = None
        request.user_role = None
        request.is_saas_superadmin = False
        request.allowed_modules = {}

        if request.user.is_authenticated:
            profile = getattr(request.user, 'restaurant_profile', None)
            request.user_role = get_user_role(request.user)
            request.is_saas_superadmin = user_is_superadmin(request.user)
            request.allowed_modules = {
                module: user_can_access_module(request.user, module)
                for module in MODULE_ROLE_MAP
            }

            if profile:
                request.restaurant = profile.restaurant

            if request.path.startswith('/admin/') and not request.is_saas_superadmin:
                return render(request, 'auth/403.html', {
                    'message': 'Solo SUPERADMIN puede acceder al admin SaaS.',
                }, status=403)

        return self.get_response(request)
