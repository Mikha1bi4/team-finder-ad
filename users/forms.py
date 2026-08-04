from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .validators import validate_phone_number, validate_github_url


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.com'
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class UserRegisterForm(UserCreationForm):
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль (минимум 8 символов)',
        })
    )

    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль',
        })
    )

    class Meta:
        model = User
        fields = ('name', 'surname', 'email', 'password1', 'password2')
        labels = {
            'name': 'Имя',
            'surname': 'Фамилия',
            'email': 'Email',
        }
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@mail.com',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше имя',
            }),
            'surname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите вашу фамилию',
            }),
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name', 'surname', 'avatar', 'about', 'phone', 'github_url')
        labels = {
            'name': 'Имя',
            'surname': 'Фамилия',
            'avatar': 'Аватар',
            'about': 'О себе',
            'phone': 'Телефон',
            'github_url': 'GitHub',
        }

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше имя',
                'maxlength': '124',
            }),
            'surname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите вашу фамилию',
                'maxlength': '124',
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'about': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Расскажите о себе...',
                'rows': 5,
                'maxlength': '256',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 999 123 45 67',
                'type': 'tel',
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username',
                'type': 'url',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Добавляем валидаторы
        self.fields['phone'].validators.append(validate_phone_number)
        self.fields['github_url'].validators.append(validate_github_url)
