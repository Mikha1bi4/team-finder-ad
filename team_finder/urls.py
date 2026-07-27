from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('projects/', include('projects.urls', namespace='projects')),
    path('users/', include('django.contrib.auth.urls')),  # Подключаем работу с пользователями 
    path(
        'users/registration/',
        CreateView.as_view(
            template_name='users/register.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('projects:list'),
        ),
        name='registration',
    ),
]
