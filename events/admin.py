from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    SportType,
    EventType,
    Location,
    Event,
    EventRegistration,
    EventResult
)


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'display_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'display_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'display_name', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'display_name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    readonly_fields = ('created_at', 'updated_at')


class SportTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address')
    list_filter = ('city',)
    search_fields = ('name', 'address', 'city')


class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 1
    can_delete = True
    readonly_fields = ('registration_datetime',)


class EventResultInline(admin.TabularInline):
    model = EventResult
    extra = 1
    can_delete = True
    readonly_fields = ('recorded_at',)


class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'sport_type', 'event_type', 'start_datetime', 'status', 'is_public')
    list_filter = ('status', 'is_public', 'sport_type', 'event_type')
    search_fields = ('title', 'description', 'organizer__email', 'organizer__display_name')
    date_hierarchy = 'start_datetime'
    readonly_fields = ('created_at', 'updated_at')
    inlines = [EventRegistrationInline, EventResultInline]


class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'registration_datetime', 'status')
    list_filter = ('status', 'registration_datetime')
    search_fields = ('event__title', 'user__email', 'user__display_name')
    readonly_fields = ('registration_datetime',)


class EventResultAdmin(admin.ModelAdmin):
    list_display = ('event', 'participant_user', 'team_name_if_applicable', 'position', 'score', 'recorded_at')
    list_filter = ('recorded_at',)
    search_fields = (
    'event__title', 'participant_user__email', 'participant_user__display_name', 'team_name_if_applicable')
    readonly_fields = ('recorded_at',)


admin.site.register(User, UserAdmin)
admin.site.register(SportType, SportTypeAdmin)
admin.site.register(EventType, EventTypeAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventRegistration, EventRegistrationAdmin)
admin.site.register(EventResult, EventResultAdmin)