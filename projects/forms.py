from django import forms
from .models import Project
from .validators import validate_github_url


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'description', 'github_url', 'status')
        labels = {
            'name': 'Имя',
            'description': 'Описание',
            'github_url': 'GitHub',
            'status': 'Статус'
        }

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название проекта',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите описание проекта',
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username/reponame',
                'type': 'url',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Выберите статус',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Добавляем валидаторы
        self.fields['github_url'].validators.append(validate_github_url)
