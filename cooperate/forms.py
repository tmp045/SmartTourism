from django import forms
from .models import Cooperation, Dish

class RestaurantPartnerForm(forms.ModelForm):
    class Meta:
        model = Cooperation
        fields = ['restaurant_name', 'phone', 'email', 'address', 'description', 'image', 'province', 'ward', "latitude", "longitude",]
        widgets = {
            'restaurant_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }
        labels = {
            'restaurant_name': 'Tên nhà hàng',
            'phone': 'Số điện thoại',
            'email': 'Email',
            'address': 'Địa chỉ',
            'description': 'Mô tả về quán',
            'image': 'Hình ảnh quán',
        }


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['name', 'description', 'price', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input', 'checked': 'checked'}),
        }
        labels = {
            'name': 'Tên món',
            'description': 'Mô tả',
            'price': 'Giá (VNĐ)',
            'image': 'Hình ảnh',
            'is_available': 'Còn hàng',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mặc định món mới là có sẵn
        if not self.instance.pk:  # Chỉ khi tạo mới (không phải edit)
            self.fields['is_available'].initial = True


