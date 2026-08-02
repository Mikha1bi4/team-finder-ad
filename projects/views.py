from django.views.generic import ListView, DetailView
from .models import Project
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


class ProjectListView(ListView):
    model = Project
    ordering = '-created_at'
    paginate_by = 12
    template_name = 'projects/project_list.html'


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project-details.html'


@login_required
def complete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if project.owner != request.user:
        return JsonResponse({'error': 'Нет прав'}, status=403)

    if project.status != 'open':
        return JsonResponse({'error': 'Проект уже завершен'}, status=400)

    project.status = 'close'
    project.save()

    return JsonResponse({"status": "ok", "project_status": "closed"})
