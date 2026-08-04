from django.urls import include, path, reverse_lazy
from .forms import UserRegisterForm, UserLoginForm
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from .views import (UserListView, UserDetailView, get_skills,
                    add_skill, remove_skill, UserUpdateView)

app_name = 'users'
urlpatterns = [
    # path('', include('django.contrib.auth.urls')),
    path(
        'register/',
        CreateView.as_view(
            template_name='users/register.html',
            form_class=UserRegisterForm,
            success_url=reverse_lazy('projects:list'),
        ),
        name='register',
    ),
    path('login/', LoginView.as_view(
         template_name='users/login.html',
         authentication_form=UserLoginForm,
         redirect_authenticated_user=True,
         next_page='projects:list'),
         name='login'),
    path('logout/', LogoutView.as_view(
        next_page='users:login'
    ), name='logout'),
    path('skills/', get_skills, name='get_skills'),
    path('list/', UserListView.as_view(), name='list'),
    path('<int:pk>/', UserDetailView.as_view(), name='detail'),
    path('edit-profile/', UserUpdateView.as_view(), name='edit-profile'),
    path('<int:pk>/skills/add/', add_skill, name='add_skill'),
    path('<int:pk>/skills/<int:skill_id>/remove/',
         remove_skill, name='remove_skill'),
]
