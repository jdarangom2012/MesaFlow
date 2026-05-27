class RestaurantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.restaurant = None

        if request.user.is_authenticated:
            profile = getattr(request.user, 'restaurant_profile', None)

            if profile:
                request.restaurant = profile.restaurant

        return self.get_response(request)
