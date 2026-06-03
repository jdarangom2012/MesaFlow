from django import forms

from restaurants.models import Restaurant

from .models import RestaurantTable


class RestaurantTableForm(forms.ModelForm):
    name = forms.CharField(
        label='Nombre mesa',
        widget=forms.TextInput(attrs={'placeholder': 'Ej. Mesa 12'}),
    )
    capacity = forms.IntegerField(
        label='Capacidad',
        min_value=1,
        widget=forms.NumberInput(attrs={'min': 1, 'step': 1}),
    )
    type = forms.ChoiceField(label='Tipo', choices=RestaurantTable.TYPE_CHOICES)
    is_active = forms.BooleanField(label='Estado activo', required=False, initial=True)
    sort_order = forms.IntegerField(
        label='Orden visual',
        min_value=0,
        widget=forms.NumberInput(attrs={'min': 0, 'step': 1}),
    )

    class Meta:
        model = RestaurantTable
        fields = ['name', 'capacity', 'type', 'is_active', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej. Mesa 12'}),
            'capacity': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'sort_order': forms.NumberInput(attrs={'min': 0, 'step': 1}),
        }

    def __init__(self, *args, include_restaurant=False, **kwargs):
        super().__init__(*args, **kwargs)

        if include_restaurant:
            self.fields['restaurant'] = forms.ModelChoiceField(
                queryset=Restaurant.objects.filter(is_active=True).order_by('name'),
                label='Restaurante',
                required=True,
            )
            if self.instance and self.instance.restaurant_id:
                self.fields['restaurant'].initial = self.instance.restaurant

            self.order_fields(['restaurant', 'name', 'capacity', 'type', 'is_active', 'sort_order'])
