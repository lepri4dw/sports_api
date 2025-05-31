from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, display_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        if not display_name:
            raise ValueError('Имя пользователя обязательно')

        email = self.normalize_email(email)
        user = self.model(email=email, display_name=display_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, display_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, display_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']

    def __str__(self):
        return self.email


class SportType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # Изменяем CharField на ImageField
    icon = models.ImageField(upload_to='sport_type_icons/', blank=True, null=True) # Изменено

    def __str__(self):
        return self.name

    # Опционально: метод для получения URL иконки
    def get_icon_url(self):
        if self.icon and hasattr(self.icon, 'url'):
            return self.icon.url
        return None


class EventType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='created_locations')

    def __str__(self):
        return f"{self.name}, {self.city}"


class Event(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Черновик'),
        ('PLANNED', 'Запланировано'),
        ('REGISTRATION_OPEN', 'Регистрация открыта'),
        ('REGISTRATION_CLOSED', 'Регистрация закрыта'),
        ('ACTIVE', 'Активно'),
        ('COMPLETED', 'Завершено'),
        ('CANCELLED', 'Отменено'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    sport_type = models.ForeignKey(SportType, on_delete=models.PROTECT)
    event_type = models.ForeignKey(EventType, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    custom_location_text = models.CharField(max_length=255, blank=True, null=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(blank=True, null=True)
    registration_deadline = models.DateTimeField(blank=True, null=True)
    max_participants = models.IntegerField(blank=True, null=True)
    current_participants_count = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PLANNED')
    is_public = models.BooleanField(default=True)
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class EventRegistration(models.Model):
    STATUS_CHOICES = (
        ('PENDING_APPROVAL', 'Ожидает подтверждения'),
        ('CONFIRMED', 'Подтверждено'),
        ('REJECTED_BY_ORGANIZER', 'Отклонено организатором'),
        ('CANCELLED_BY_USER', 'Отменено пользователем'),
        ('ATTENDED', 'Посетил'),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    registration_datetime = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING_APPROVAL')
    notes_by_user = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('event', 'user')  # Один пользователь не может зарегистрироваться дважды на одно мероприятие

    def __str__(self):
        return f"{self.user.display_name} - {self.event.title}"


class EventResult(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='results')
    participant_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='event_results')
    team_name_if_applicable = models.CharField(max_length=100, blank=True, null=True)
    position = models.IntegerField(blank=True, null=True)
    score = models.CharField(max_length=100, blank=True, null=True)
    achievement_description = models.TextField(blank=True, null=True)
    recorded_by_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recorded_results')
    recorded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        participant = self.participant_user.display_name if self.participant_user else self.team_name_if_applicable
        return f"{participant} - {self.event.title}"