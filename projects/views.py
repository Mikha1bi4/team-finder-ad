from django.views.generic import ListView, DetailView
from .models import Project
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


class ProjectListView(ListView):
    model = Project
    ordering = '-created_at'
    paginate_by = 12
    template_name = 'projects/project_list.html'


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project-details.html'


@login_required
@require_POST
def complete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if project.owner != request.user:
        return JsonResponse({'error': 'Нет прав'}, status=403)

    if project.status != 'open':
        return JsonResponse({'error': 'Проект уже завершен'}, status=400)

    project.status = 'closed'
    project.save()

    return JsonResponse({"status": "ok", "project_status": "closed"})


@login_required
@require_POST
def toggle_participate(request, pk):
    project = get_object_or_404(Project, pk=pk)

    is_participating = request.user in project.participants.all()

    if is_participating:
        project.participants.remove(request.user)
        message = 'Вы вышли из проекта'
    else:
        project.participants.add(request.user)
        message = 'Вы присоединились к проекту'

    return JsonResponse({
        "status": "ok",
        "message": message,
        "is_participating": not is_participating,
        "participants_count": project.participants.count(),
        "participant": {
            "id": request.user.id,
            "name": request.user.name,
            "avatar": getattr(request.user, 'avatar_url', ''),
        } if not is_participating else None  # Если добавили, возвращаем данные
    })
