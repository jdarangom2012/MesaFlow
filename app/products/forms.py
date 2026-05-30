from django import forms

from .models import Product, ProductCategory


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'icon', 'color', 'is_active', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej. Pizzas'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción interna o visible de la categoría'}),
            'icon': forms.TextInput(attrs={'placeholder': 'Ej. 🍕'}),
            'color': forms.TextInput(attrs={'placeholder': '#00E5FF'}),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'category',
            'price',
            'icon',
            'color',
            'image',
            'is_active',
            'is_pos_available',
            'is_kitchen_available',
            'sort_order',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej. Producto destacado'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción visible para POS y menú'}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'icon': forms.TextInput(attrs={'placeholder': 'Ej. 🍕'}),
            'color': forms.TextInput(attrs={'placeholder': '#00E5FF'}),
            'sort_order': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, restaurant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if restaurant is not None:
            self.fields['category'].queryset = (
                ProductCategory.objects
                .filter(restaurant=restaurant)
                .order_by('sort_order', 'name')
            )
