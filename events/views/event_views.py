from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q

from ..models import Event, EventRegistration, EventResult
from ..serializers import (
    EventSerializer,
    EventDetailSerializer,
    EventRegistrationSerializer,
    EventResultSerializer
)


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Пользовательское разрешение для проверки, является ли пользователь организатором события.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, HEAD и OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем PUT/DELETE только организатору
        return obj.organizer == request.user


class IsAuthenticatedForRegister(permissions.BasePermission):
    """
    Пользовательское разрешение для регистрации на мероприятия.
    Требует только аутентификации, без проверки организатора.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class EventViewSet(viewsets.ModelViewSet):
    """
    API для создания, редактирования и получения информации о мероприятиях.
    """
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sport_type', 'event_type', 'status', 'is_public']
    search_fields = ['title', 'description']
    ordering_fields = ['start_datetime', 'created_at']
    ordering = ['start_datetime']

    def get_permissions(self):
        """
        Получение разрешений для разных операций:
        - GET запросы могут выполнять все пользователи
        - POST/PUT/DELETE запросы требуют аутентификации
        - PUT/DELETE запросы могут выполнять только организаторы
        - Регистрация/отмена регистрации требуют только аутентификации
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['create', 'register', 'unregister']:
            permission_classes = [IsAuthenticatedForRegister]
        else:
            permission_classes = [IsOrganizerOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Фильтрация событий по параметрам запроса.
        """
        queryset = Event.objects.all()

        # Фильтр по умолчанию: только публичные мероприятия, если не указано иное
        if not self.request.query_params.get('include_private', False):
            queryset = queryset.filter(is_public=True)

        # Фильтрация по городу (через location)
        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(location__city__icontains=city)

        # Фильтрация по дате
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(start_datetime__gte=date_from)

        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(start_datetime__lte=date_to)

        return queryset

    def get_serializer_class(self):
        """
        Использование разных сериализаторов для разных действий.
        """
        if self.action == 'retrieve':
            return EventDetailSerializer
        return EventSerializer

    def perform_create(self, serializer):
        """
        Установка организатора при создании мероприятия.
        """
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedForRegister])
    def register(self, request, pk=None):
        """
        Регистрация на мероприятие.
        """
        event = self.get_object()

        # Проверка наличия существующей регистрации перед сериализацией
        if EventRegistration.objects.filter(event=event, user=request.user).exists():
            return Response(
                {"error": "Вы уже зарегистрированы на это мероприятие"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка статуса мероприятия до валидации
        if event.status not in ['PLANNED', 'REGISTRATION_OPEN']:
            return Response(
                {"error": f"Регистрация недоступна. Текущий статус: {event.get_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка максимального количества участников
        if event.max_participants and event.current_participants_count >= event.max_participants:
            return Response(
                {"error": "Достигнуто максимальное количество участников"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Добавляем event_id в данные запроса
        data = request.data.copy()
        data['event_id'] = event.id

        serializer = EventRegistrationSerializer(
            data=data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # Более информативное сообщение об ошибке
        return Response(
            {"error": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticatedForRegister])
    def unregister(self, request, pk=None):
        """
        Отмена регистрации на мероприятие.
        """
        event = self.get_object()
        try:
            registration = EventRegistration.objects.get(event=event, user=request.user)
        except EventRegistration.DoesNotExist:
            return Response(
                {"error": "Вы не зарегистрированы на это мероприятие"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Меняем статус на отмененный пользователем
        registration.status = 'CANCELLED_BY_USER'
        registration.save()

        # Уменьшаем счетчик участников
        event.current_participants_count = max(0, event.current_participants_count - 1)
        event.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def registrations(self, request, pk=None):
        """
        Получение списка регистраций для мероприятия (только для организатора).
        """
        event = self.get_object()

        # Проверка, что текущий пользователь - организатор
        if event.organizer != request.user:
            return Response(
                {"error": "Только организатор может просматривать список регистраций"},
                status=status.HTTP_403_FORBIDDEN
            )

        registrations = EventRegistration.objects.filter(event=event)
        serializer = EventRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_result(self, request, pk=None):
        """
        Добавление результата мероприятия (только для организатора).
        """
        event = self.get_object()

        # Проверка, что текущий пользователь - организатор
        if event.organizer != request.user:
            return Response(
                {"error": "Только организатор может добавлять результаты"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Добавляем event_id в данные запроса
        data = request.data.copy()
        data['event_id'] = event.id

        serializer = EventResultSerializer(
            data=data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            {"error": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class EventRegistrationViewSet(viewsets.ModelViewSet):
    """
    API для управления регистрациями на мероприятия.
    """
    serializer_class = EventRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Пользователи видят только свои регистрации
        """
        if self.request.user.is_authenticated:
            return EventRegistration.objects.filter(user=self.request.user)
        return EventRegistration.objects.none()

    @action(detail=True, methods=['put'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Обновление статуса регистрации (только для организатора).
        """
        registration = self.get_object()
        event = registration.event

        # Проверка, что текущий пользователь - организатор
        if event.organizer != request.user:
            return Response(
                {"error": "Только организатор может изменять статус регистрации"},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        if not new_status or new_status not in [s[0] for s in EventRegistration.STATUS_CHOICES]:
            return Response(
                {"error": "Необходимо указать корректный статус"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Если статус меняется с подтвержденного на отклоненный - уменьшаем счетчик
        if registration.status == 'CONFIRMED' and new_status == 'REJECTED_BY_ORGANIZER':
            event.current_participants_count = max(0, event.current_participants_count - 1)
            event.save()

        # Если статус меняется с неподтвержденного на подтвержденный - увеличиваем счетчик
        elif registration.status != 'CONFIRMED' and new_status == 'CONFIRMED':
            event.current_participants_count += 1
            event.save()

        registration.status = new_status
        registration.save()

        serializer = EventRegistrationSerializer(registration)
        return Response(serializer.data)


class EventResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для получения результатов мероприятий.
    """
    serializer_class = EventResultSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Фильтрация результатов по мероприятию
        """
        queryset = EventResult.objects.all()

        event_id = self.request.query_params.get('event_id', None)
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        return queryset