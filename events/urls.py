from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    user_views,
    catalog_views,
    event_views
)

# Создаем router для DRF ViewSets
router = DefaultRouter()
router.register(r'sport-types', catalog_views.SportTypeViewSet)
router.register(r'event-types', catalog_views.EventTypeViewSet)
router.register(r'locations', catalog_views.LocationViewSet)
router.register(r'events', event_views.EventViewSet, basename='event')
router.register(r'registrations', event_views.EventRegistrationViewSet, basename='registration')
router.register(r'results', event_views.EventResultViewSet, basename='result')

urlpatterns = [
    # Пользовательские маршруты
    path('users/me/', user_views.UserProfileView.as_view(), name='user-profile'),

    # Включаем все маршруты из router
    path('', include(router.urls)),
]