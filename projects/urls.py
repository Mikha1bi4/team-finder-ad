from django.urls import path
from .views import ProjectListView, ProjectDetailView, complete_project, toggle_participate

app_name = 'projects'
urlpatterns = [
    path('list/', ProjectListView.as_view(), name='list'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/complete/', complete_project, name='complete'),
    path('<int:pk>/toggle-participate/',  toggle_participate, name='toggle-participate')

]
