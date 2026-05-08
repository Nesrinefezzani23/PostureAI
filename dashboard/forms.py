from django import forms
from .models import Profile

class EssentialProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['taille_cm', 'activite']
        widgets = {
            'taille_cm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 175'}),
            'activite': forms.Select(attrs={'class': 'form-select'}),
        }

class DetailedProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['taille_cm', 'activite', 'pathologies', 'objectifs']
        widgets = {
            'taille_cm': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 175'}),
            'activite': forms.Select(attrs={'class': 'form-select'}),
            'pathologies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Scoliose, Hernie...'}),
            'objectifs': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Réduire mes douleurs cervicales...'}),
        }

