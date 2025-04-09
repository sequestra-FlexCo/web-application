from django import forms
from .models import *

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['name', 'rpm']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Session Name'}),
            'rpm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'RPM'}),
        }
        
