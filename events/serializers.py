from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import SportType, EventType, Location, Event, EventRegistration, EventResult

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'display_name', 'password', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            display_name=validated_data['display_name'],
            password=validated_data['password']
        )
        return user


class SportTypeSerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField() # Поле для URL

    class Meta:
        model = SportType
        fields = ['id', 'name', 'description', 'icon', 'icon_url'] # 'icon' для загрузки, 'icon_url' для чтения
        read_only_fields = ['icon_url'] # icon_url только для чтения
        extra_kwargs = {
            'icon': {'write_only': True, 'required': False} # icon только для записи, не обязательное
        }

    def get_icon_url(self, obj):
        request = self.context.get('request')
        if obj.icon and hasattr(obj.icon, 'url'):
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url # Возвращаем относительный URL, если нет request
        return None


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    created_by_user = UserSerializer(read_only=True)

    class Meta:
        model = Location
        fields = '__all__'
        read_only_fields = ['created_by_user']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by_user'] = user
        return super().create(validated_data)


# Определение EventSerializer до его использования другими сериализаторами
class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    sport_type = SportTypeSerializer(read_only=True)
    sport_type_id = serializers.IntegerField(write_only=True)
    event_type = EventTypeSerializer(read_only=True)
    event_type_id = serializers.IntegerField(write_only=True)
    location = LocationSerializer(read_only=True)
    location_id = serializers.IntegerField(write_only=True, required=False)
    registrations_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'organizer', 'sport_type', 'sport_type_id',
                  'event_type', 'event_type_id', 'location', 'location_id', 'custom_location_text',
                  'start_datetime', 'end_datetime', 'registration_deadline', 'max_participants',
                  'current_participants_count', 'registrations_count', 'status', 'is_public',
                  'entry_fee', 'contact_email', 'contact_phone', 'created_at', 'updated_at']
        read_only_fields = ['id', 'organizer', 'current_participants_count', 'created_at', 'updated_at']

    def get_registrations_count(self, obj):
        return obj.registrations.count()

    def validate(self, data):
        # Проверка дат
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        registration_deadline = data.get('registration_deadline')

        if end_datetime and start_datetime and end_datetime <= start_datetime:
            raise serializers.ValidationError("Дата окончания должна быть позже даты начала")

        if registration_deadline and start_datetime and registration_deadline >= start_datetime:
            raise serializers.ValidationError("Дедлайн регистрации должен быть раньше даты начала")

        return data

    def create(self, validated_data):
        validated_data['organizer'] = self.context['request'].user
        return super().create(validated_data)


class EventRegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    # Используем вложенный сериализатор для вывода данных
    event = EventSerializer(read_only=True)
    
    # Поле для принятия ID события при создании регистрации
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        write_only=True,
        source='event'
    )

    class Meta:
        model = EventRegistration
        fields = ['id', 'event', 'event_id', 'user', 'user_id', 'registration_datetime', 'status', 'notes_by_user']
        read_only_fields = ['id', 'registration_datetime']

    def validate(self, data):
        # Получаем мероприятие (теперь оно уже доступно как data['event'])
        event = data['event']
        user = self.context['request'].user

        # Проверяем, добавляет ли организатор участника
        is_organizer_adding_participant = 'user_id' in data and user.id == event.organizer.id
        
        # Если организатор добавляет участника, пропускаем проверку на организатора
        if 'user_id' in data and not is_organizer_adding_participant:
            # Организатор может добавлять участников на своё мероприятие
            raise serializers.ValidationError("Только организатор может добавлять участников")
        elif not is_organizer_adding_participant:
            # Если пользователь регистрируется сам и он организатор этого мероприятия
            if event.organizer == user:
                raise serializers.ValidationError("Организатор не может зарегистрироваться на своё мероприятие")

        # Проверка статуса мероприятия
        if event.status not in ['PLANNED', 'REGISTRATION_OPEN']:
            raise serializers.ValidationError("Регистрация на это мероприятие недоступна")

        # Проверка срока регистрации
        if event.registration_deadline and event.registration_deadline < timezone.now():
            raise serializers.ValidationError("Срок регистрации истек")

        # Проверка максимального количества участников
        if event.max_participants and event.current_participants_count >= event.max_participants:
            raise serializers.ValidationError("Достигнуто максимальное количество участников")

        return data

    def create(self, validated_data):
        user_id = validated_data.pop('user_id', None)
        user = self.context['request'].user if not user_id else User.objects.get(id=user_id)

        # Проверка существования регистрации
        event = validated_data.get('event')
        if EventRegistration.objects.filter(event=event, user=user).exists():
            raise serializers.ValidationError("Вы уже зарегистрированы на это мероприятие")

        registration = EventRegistration.objects.create(user=user, **validated_data)

        # Увеличение счетчика участников
        event.current_participants_count += 1
        event.save()

        return registration


class EventResultSerializer(serializers.ModelSerializer):
    participant_user = UserSerializer(read_only=True)
    participant_user_id = serializers.IntegerField(write_only=True, required=False)
    recorded_by_user = UserSerializer(read_only=True)
    
    # Используем вложенный сериализатор для вывода данных
    event = EventSerializer(read_only=True)
    
    # Поле для принятия ID события при создании результата
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        write_only=True,
        source='event'
    )

    class Meta:
        model = EventResult
        fields = ['id', 'event', 'event_id', 'participant_user', 'participant_user_id', 'team_name_if_applicable',
                  'position', 'score', 'achievement_description', 'recorded_by_user', 'recorded_at']
        read_only_fields = ['id', 'recorded_by_user', 'recorded_at']

    def validate(self, data):
        # Мероприятие уже доступно как data['event']
        event = data['event']
        user = self.context['request'].user

        if event.organizer != user:
            raise serializers.ValidationError("Только организатор может добавлять результаты")

        # Проверка статуса мероприятия
        if event.status not in ['ACTIVE', 'COMPLETED']:
            raise serializers.ValidationError(
                "Результаты можно добавлять только для активных или завершенных мероприятий")

        # Если указан участник, проверить, что он зарегистрирован
        participant_user_id = data.get('participant_user_id')
        if participant_user_id:
            if not EventRegistration.objects.filter(
                    event=event,
                    user_id=participant_user_id,
                    status__in=['CONFIRMED', 'ATTENDED']
            ).exists():
                raise serializers.ValidationError("Этот пользователь не зарегистрирован на мероприятие")

        return data

    def create(self, validated_data):
        participant_user_id = validated_data.pop('participant_user_id', None)
        if participant_user_id:
            validated_data['participant_user'] = User.objects.get(id=participant_user_id)

        validated_data['recorded_by_user'] = self.context['request'].user
        return super().create(validated_data)


class EventDetailSerializer(EventSerializer):
    registrations = EventRegistrationSerializer(many=True, read_only=True)
    results = EventResultSerializer(many=True, read_only=True)

    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + ['registrations', 'results']