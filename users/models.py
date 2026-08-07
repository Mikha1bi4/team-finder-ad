from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageDraw, ImageFont
import random
from io import BytesIO
from django.core.files.base import ContentFile


def generate_avatar(name, email):
    email = email.replace('.', '').replace('@', '')
    size = 200
    colors = [
        (200, 180, 230),
        (220, 190, 240),
        (190, 170, 220),
        (180, 200, 230),
        (190, 215, 235),
        (170, 195, 225),
        (200, 220, 240),
        (200, 220, 180),
        (190, 215, 175),
        (210, 230, 190),
        (180, 210, 195),
        (230, 180, 180),
        (240, 190, 200),
        (225, 175, 185),
        (235, 200, 200),
        (230, 210, 170),
        (240, 220, 180),
        (235, 215, 175),
        (225, 200, 160),
        (230, 190, 170),
        (240, 200, 180),
        (225, 185, 165),
        (235, 205, 185),
        (210, 210, 220),
        (200, 200, 210),
        (215, 215, 215),
        (195, 195, 205),
        (170, 215, 215),
        (185, 210, 215),
        (175, 205, 200),
        (190, 220, 215),
        (220, 180, 210),
        (210, 185, 215),
        (225, 195, 215),
        (215, 190, 220),
    ]
    bg = random.choice(colors)

    img = Image.new('RGB', (size, size), bg)
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size//2)

    text = name[0].upper()

    # Используем anchor для центрирования
    # 'mm' означает middle-middle (центр по вертикали и горизонтали)
    draw.text((size//2, size//2), text, fill=(255, 255, 255),
              font=font, anchor='mm')

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), name=f'avatar_{email}.png')


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
        default='avatars/default-avatar.png'
    )

    # В рекомендациях написано, что это обязательное поле,
    #  но при регистрации оно не запрашивается
    phone = models.CharField(max_length=12, null=True, blank=True)
    github_url = models.URLField(blank=True, null=True)
    about = models.TextField(max_length=256, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    favorites = models.ManyToManyField('projects.Project',
                                       blank=True,
                                       related_name='interested_users')
    skills = models.ManyToManyField(Skill, blank=True, related_name='users')

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname']

    objects = CustomUserManager()

    def __str__(self):
        if self.name and self.surname:
            return f"{self.name} {self.surname}"
        return self.email

    def save(self, *args, **kwargs):
        if not self.pk:
           self.avatar = generate_avatar(self.name, self.email)
        super().save(*args, **kwargs)
