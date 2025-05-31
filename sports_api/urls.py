# your_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Импортируем settings
from django.conf.urls.static import static # Импортируем static

from events.views import auth_views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('events.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/register/', auth_views.RegisterView.as_view(), name='register'),
    path('api/users/login/', auth_views.LoginView.as_view(), name='login'),
]

# Добавляем раздачу медиафайлов в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)