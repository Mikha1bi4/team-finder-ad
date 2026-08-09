from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import Project
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import ProjectForm
from django.shortcuts import render
from django.urls import reverse_lazy
from users.models import Skill
import json
from django.contrib.auth.mixins import LoginRequiredMixin


class ProjectListView(ListView):
    model = Project
    ordering = '-created_at'
    paginate_by = 12
    template_name = 'projects/project_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        skill = self.request.GET.get('skill')

        if skill:
            queryset = queryset.filter(
                skills__name=skill).order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_skill = self.request.GET.get('skill', '')
        context['active_skill'] = active_skill
        context['all_skills'] = Skill.objects.values_list('name', flat=True)

        return context


class FavoritesProjectsListView(LoginRequiredMixin, ListView):
    model = Project
    ordering = '-created_at'
    paginate_by = 12
    template_name = 'projects/favorite_projects.html'

    def get_queryset(self):
        queryset = self.request.user.favorites.all().order_by('-created_at')
        return queryset


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
    is_participating = project.participants.filter(id=request.user.id).exists()

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


@login_required
@require_POST
def toggle_favorite(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.user.favorites.filter(id=pk).exists():
        request.user.favorites.remove(project)
        favorited = "Не избранный"
    else:
        request.user.favorites.add(project)
        favorited = "Избранный"
    return JsonResponse({"status": "ok", "favorited": favorited})


class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create-project.html'

    def form_valid(self, form):
        project = form.save(commit=False)
        project.owner = self.request.user
        project.save()
        project.participants.add(self.request.user)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.method == 'GET':
            context['is_edit'] = False

        return context

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})


class ProjectUpdateView(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create-project.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})


@login_required
@require_POST
def add_skill(request, pk):
    created = False
    added = True

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Неверный формат JSON'
        }, status=400)

    skill_name = data.get('name', '').strip()
    skill_id = data.get('skill_id', '').strip()

    project = get_object_or_404(Project, pk=pk)
    if request.user.id != project.owner.id:
        return JsonResponse({'error': 'Отказано в доступе'}, status=403)

    if not skill_id and not skill_name:
        return JsonResponse({
            'status': 'error',
            'message': 'Укажите name или id навыка'
        }, status=400)

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
        if not request.user.skills.filter(id=skill_id).exists():
            project.skills.add(skill)
            skill_name = skill.name
        else:
            added = False
    elif skill_name:
        new_skill = Skill.objects.create(name=skill_name)
        project.skills.add(new_skill)
        skill_id = new_skill.id
        created = True

    return JsonResponse(
        {'id': skill_id, 'name': skill_name,
         'created': created, 'added': added})


@login_required
@require_POST
def remove_skill(request, pk, skill_id):

    project = get_object_or_404(Project, pk=pk)
    if request.user.id != project.owner.id:
        return JsonResponse({'error': 'Отказано в доступе'}, status=403)

    if not Skill.objects.filter(id=skill_id).exists():
        return JsonResponse(
            {'error': f'Не существует навыка с id: {skill_id}'}, status=404)

    if not project.skills.filter(id=skill_id).exists():
        return JsonResponse(
                    {'error':
                     f"""
                     Проект {project.name}
                     не обладает навыком с id: {skill_id}
                     """
                     }, status=404)

    project.skills.remove(skill_id)
    return JsonResponse({'status': 'ok'})
