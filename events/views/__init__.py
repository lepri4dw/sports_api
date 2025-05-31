# Импортируем представления для удобного доступа
from .auth_views import RegisterView, LoginView
from .user_views import UserProfileView
from .catalog_views import SportTypeViewSet, EventTypeViewSet, LocationViewSet
from .event_views import EventViewSet, EventRegistrationViewSet, EventResultViewSet