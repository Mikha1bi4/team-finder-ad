from django.contrib import admin
from django.urls import path, reverse_lazy, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy('projects:list')),
         name='home'),
    path('admin/', admin.site.urls),
    path('projects/', include('projects.urls', namespace='projects')),
    path('users/', include('users.urls', namespace='users')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
