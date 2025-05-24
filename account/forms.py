from .models import Ad
from django import forms
# VERY SIMPLE FORM FOR AD/EDIT AD
class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = [
            'title',
            'description',
            'category',
            'condition'
        ]
        widgets = {
            'category': forms.Select(),
            'condition': forms.Select(),
            'title': forms.TextInput(attrs={
                'placeholder': 'Название'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Описание предмета',
                'rows': '4'
            })
        }
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'category': 'Категория',
            'condition': 'Состояние'
        }

class SearchForm(forms.Form):
    query = forms.CharField()