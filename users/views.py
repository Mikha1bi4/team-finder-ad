from django.views.generic import ListView
from .models import User, Skill


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
