from django.core.exceptions import ObjectDoesNotExist


def restaurant_settings(request):
    restaurant = getattr(request, 'restaurant', None)
    settings = None

    if restaurant:
        try:
            settings = restaurant.settings
        except ObjectDoesNotExist:
            settings = None

    restaurant_name = restaurant.name if restaurant else 'MesaFlow'
    restaurant_logo = ''
    primary_color = '#00E5FF'
    secondary_color = '#081028'

    if settings:
        primary_color = settings.primary_color or primary_color
        secondary_color = settings.secondary_color or secondary_color

        if settings.logo:
            restaurant_logo = settings.logo.url

    return {
        'restaurant_settings': settings,
        'restaurant_name': restaurant_name,
        'restaurant_logo': restaurant_logo,
        'primary_color': primary_color,
        'secondary_color': secondary_color,
    }
