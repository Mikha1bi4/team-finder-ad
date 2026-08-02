from django.urls import include, path, reverse_lazy
from .forms import UserRegisterForm, UserLoginForm
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from .views import UserListView

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
    path('list/', UserListView.as_view(
         template_name='users/participants.html'), name='list'),
]
