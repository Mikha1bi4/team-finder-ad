from django.db import models
from users.models import User


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    github_url = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=6, choices=Status.choices)
    participants = models.ManyToManyField(
        User,
        related_name='participating_projects')
