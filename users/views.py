from django.views.generic import ListView, DetailView, UpdateView
from .models import User, Skill
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
import json
from .forms import UserUpdateForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class UserListView(ListView):
    model = User
    ordering = 'id'
    paginate_by = 12
    template_name = 'users/participants.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        skill = self.request.GET.get('skill')

        if skill:
            queryset = queryset.filter(
                skills__name__icontains=skill).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["participants"] = self.get_queryset()
        context["all_skills"] = Skill.objects.all()

        skill = self.request.GET.get('skill')
        if skill:
            context["active_skill"] = skill
        return context


class UserDetailView(DetailView):
    model = User
    template_name = 'users/user-details.html'


def get_skills(request):
    s = request.GET.get('q', '')
    if not s or len(s) < 2:
        return JsonResponse([], safe=False)

    skills = Skill.objects.filter(name__startswith=s).order_by('name')[:10]
    return JsonResponse(list(skills.values('id', 'name')), safe=False)


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'users/edit_profile.html'

    def get_object(self, queryset=None):
        """Всегда возвращаем текущего пользователя"""
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('users:detail', kwargs={'pk': self.object.pk})

    def test_func(self):
        user = self.get_object()
        return self.request.user == user


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

    if request.user.id != pk:
        return JsonResponse({'error': 'Отказано в доступе'}, status=403)

    if not skill_id and not skill_name:
        return JsonResponse({
            'status': 'error',
            'message': 'Укажите name или id навыка'
        }, status=400)

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
        if not request.user.skills.filter(id=skill_id).exists():
            request.user.skills.add(skill)
            skill_name = skill.name
        else:
            added = False
    elif skill_name:
        new_skill = Skill.objects.create(name=skill_name)
        request.user.skills.add(new_skill)
        skill_id = new_skill.id
        created = True

    return JsonResponse(
        {'id': skill_id, 'name': skill_name,
         'created': created, 'added': added})


@login_required
@require_POST
def remove_skill(request, pk, skill_id):

    if request.user.id != pk:
        return JsonResponse({'error': 'Отказано в доступе'}, status=403)

    if not Skill.objects.filter(id=skill_id).exists():
        return JsonResponse(
            {'error': f'Не существует навыка с id: {skill_id}'}, status=404)

    if not request.user.skills.filter(id=skill_id).exists():
        return JsonResponse(
                    {'error':
                     f"""
                     Пользователь {request.user.name} {request.user.surname}
                     не обладает навыком с id: {skill_id}
                     """
                     }, status=404)

    request.user.skills.remove(skill_id)
    return JsonResponse({'status': 'ok'})
