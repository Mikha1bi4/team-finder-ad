from django.urls import path
from .views import (ProjectListView, ProjectDetailView,
                    complete_project, toggle_participate,
                    ProjectCreateView, ProjectUpdateView,
                    toggle_favorite, FavoritesProjectsListView,
                    add_skill, remove_skill)
from users.views import get_skills

app_name = 'projects'
urlpatterns = [
     path('list/', ProjectListView.as_view(), name='list'),
     path('create-project/', ProjectCreateView.as_view(),
          name='create-project'),
     path('favorites/', FavoritesProjectsListView.as_view(), name='favorites'),
     path('<int:pk>/', ProjectDetailView.as_view(), name='detail'),
     path('<int:pk>/edit/', ProjectUpdateView.as_view(), name='edit'),
     path('<int:pk>/complete/', complete_project, name='complete'),
     path('<int:pk>/toggle-participate/',
          toggle_participate, name='toggle-participate'),
     path('<int:pk>/toggle-favorite/',
          toggle_favorite, name='toggle-favorite'),
     path('skills/', get_skills, name='get_skills'),
     path('<int:pk>/skills/add/', add_skill, name='add_skill'),
     path('<int:pk>/skills/<int:skill_id>/remove/',
          remove_skill, name='remove_skill'),

]
