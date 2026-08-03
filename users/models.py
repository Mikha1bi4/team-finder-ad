from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер пользователей,
    где email используется как уникальный идентификатор.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Создаёт и сохраняет обычного пользователя.
        """
        if not email:
            raise ValueError(_('Email обязателен для регистрации'))

        email = self.normalize_email(email)
        extra_fields.setdefault('name', '')
        extra_fields.setdefault('surname', '')
        extra_fields.setdefault('phone', '')

        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Хешируем пароль
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Создаёт и сохраняет суперпользователя (админа).
        """

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        extra_fields.setdefault('name', 'Admin')
        extra_fields.setdefault('surname', 'Superuser')
        extra_fields.setdefault('phone', '0000000000')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Суперпользователь должен иметь is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_(
                'Суперпользователь должен иметь is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class Skill(models.Model):
    name = models.CharField(max_length=124, unique=True)

    def __str__(self):
        return self.name


class User(AbstractBaseUser,  PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        # Если не передана картинка,
        #  то нужно сгенерировать по умолчанию и положить ее в бд
        null=True
    )

    # В рекомендациях написано, что это обязательное поле,
    #  но при регистрации оно не запрашивается
    phone = models.CharField(max_length=12, null=True)
    github_url = models.URLField(blank=True, null=True)
    about = models.TextField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    skills = models.ManyToManyField(Skill, blank=True, related_name='users')

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname']

    objects = CustomUserManager()

    def __str__(self):
        if self.name and self.surname:
            return f"{self.name} {self.surname}"
        return self.email
