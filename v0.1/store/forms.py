from django import forms
from .models import ShippingAddress

class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = [
            'first_name',
            'last_name',
            'email',
            'address',
            'city',
            'state',
            'zip_code',
            'phone'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'})
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit():
            raise forms.ValidationError('Phone number must contain only digits')
        return phone

    def clean_zip_code(self):
        zip_code = self.cleaned_data.get('zip_code')
        if not zip_code.isdigit():
            raise forms.ValidationError('ZIP code must contain only digits')
        return zip_code 