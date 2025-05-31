from rest_framework import viewsets, permissions
from ..models import SportType, EventType, Location
from ..serializers import SportTypeSerializer, EventTypeSerializer, LocationSerializer


class SportTypeViewSet(viewsets.ModelViewSet): # Изменено на ModelViewSet
    """
    Получение, создание, обновление и удаление видов спорта.
    """
    queryset = SportType.objects.all()
    serializer_class = SportTypeSerializer
    # parser_classes = (MultiPartParser, FormParser) # DRF часто сам добавляет, но можно явно указать

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()] # Например, только админ может менять


class EventTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Получение списка типов мероприятий.
    """
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer
    permission_classes = [permissions.AllowAny]


class LocationViewSet(viewsets.ModelViewSet):
    """
    Получение, создание, обновление и удаление мест проведения.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    def get_permissions(self):
        """
        Получение разрешений для разных операций:
        - GET запросы могут выполнять все пользователи
        - POST/PUT/DELETE запросы только для аутентифицированных пользователей
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Фильтрация локаций по городу, если указан параметр city
        """
        queryset = Location.objects.all()
        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(city__icontains=city)
        return queryset