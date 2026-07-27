from django.views.generic import ListView
from .models import Project


class ProjectListView(ListView):
    model = Project
    ordering = '-created_at'
    paginate_by = 12
