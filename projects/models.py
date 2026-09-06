from django.db import models
from users.models import User, Skill
from .validators import validate_github_url


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Открыт'
        CLOSED = 'closed', 'Закрыт'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    github_url = models.URLField(blank=True, null=True,
                                 validators=[validate_github_url])
    status = models.CharField(max_length=6, choices=Status.choices)
    participants = models.ManyToManyField(
        User,
        related_name='participating_projects')
    skills = models.ManyToManyField(Skill, blank=True, related_name='projects')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
