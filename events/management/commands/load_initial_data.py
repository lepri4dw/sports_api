from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

# Импортируем все нужные модели
from events.models import SportType, EventType, Location, Event, EventRegistration, EventResult
from django.contrib.auth import get_user_model  # Используем get_user_model для User

User = get_user_model()


class Command(BaseCommand):
    help = 'Загружает начальные данные для справочников и тестовые данные для приложения'

    def handle(self, *args, **options):
        self.stdout.write('Начало загрузки данных...')

        # --- 1. Пользователи ---
        self.stdout.write('Создание пользователей...')
        user1_data = {'email': 'organizer_ivan@example.com', 'display_name': 'Иван Организатор',
                      'password': 'password123'}
        user2_data = {'email': 'participant_maria@example.com', 'display_name': 'Мария Участница',
                      'password': 'password123'}
        user3_data = {'email': 'spectator_oleg@example.com', 'display_name': 'Олег Зритель', 'password': 'password123'}
        user4_data = {'email': 'pro_gamer_alex@example.com', 'display_name': 'Алексей Прогеймер',
                      'password': 'password123'}

        # Создаем или получаем пользователей
        user_ivan, created = User.objects.get_or_create(
            email=user1_data['email'],
            defaults={'display_name': user1_data['display_name']}
        )
        if created: user_ivan.set_password(user1_data['password']); user_ivan.save()

        user_maria, created = User.objects.get_or_create(
            email=user2_data['email'],
            defaults={'display_name': user2_data['display_name']}
        )
        if created: user_maria.set_password(user2_data['password']); user_maria.save()

        user_oleg, created = User.objects.get_or_create(
            email=user3_data['email'],
            defaults={'display_name': user3_data['display_name']}
        )
        if created: user_oleg.set_password(user3_data['password']); user_oleg.save()

        user_alex, created = User.objects.get_or_create(
            email=user4_data['email'],
            defaults={'display_name': user4_data['display_name']}
        )
        if created: user_alex.set_password(user4_data['password']); user_alex.save()

        # Создаем суперпользователя, если его нет
        if not User.objects.filter(email='admin@example.com').exists():
            admin_user = User.objects.create_superuser('admin@example.com', 'Администратор', 'adminpass123')
            self.stdout.write(self.style.SUCCESS(f'Суперпользователь {admin_user.email} создан.'))
        else:
            admin_user = User.objects.get(email='admin@example.com')
            self.stdout.write(self.style.WARNING(f'Суперпользователь {admin_user.email} уже существует.'))

        self.stdout.write(self.style.SUCCESS('Пользователи созданы/получены.'))

        # --- 2. Виды спорта (дополненные) ---
        self.stdout.write('Создание видов спорта...')
        sport_types_data = [
            {'name': 'Футбол', 'description': 'Командный вид спорта с мячом', 'icon_url': 'icons/football.png'},
            {'name': 'Баскетбол', 'description': 'Командная игра с мячом и корзинами',
             'icon_url': 'icons/basketball.png'},
            {'name': 'Волейбол', 'description': 'Командная игра с мячом через сетку',
             'icon_url': 'icons/volleyball.png'},
            {'name': 'Теннис', 'description': 'Игра с мячом и ракетками', 'icon_url': 'icons/tennis.png'},
            {'name': 'Шахматы', 'description': 'Настольная логическая игра', 'icon_url': 'icons/chess.png'},
            {'name': 'Бег', 'description': 'Легкоатлетический вид спорта', 'icon_url': 'icons/running.png'},
            {'name': 'Йога', 'description': 'Духовные и физические практики', 'icon_url': 'icons/yoga.png'},
            {'name': 'Плавание', 'description': 'Водный вид спорта', 'icon_url': 'icons/swimming.png'},
            {'name': 'Бокс', 'description': 'Контактный боевой вид спорта', 'icon_url': 'icons/boxing.png'},
            {'name': 'Велоспорт', 'description': 'Спортивные дисциплины с использованием велосипеда',
             'icon_url': 'icons/cycling.png'},
            {'name': 'Киберспорт', 'description': 'Соревнования по компьютерным играм',
             'icon_url': 'icons/esports.png'},
            {'name': 'Падел-теннис', 'description': 'Ракетный вид спорта, сочетающий элементы тенниса и сквоша',
             'icon_url': 'icons/padel.png'}
        ]

        created_sport_types = {}
        for sport_data in sport_types_data:
            sport_type_obj, created = SportType.objects.update_or_create(
                name=sport_data['name'],
                defaults={
                    'description': sport_data['description'],
                    # Если файл уже существует в MEDIA_ROOT, можно просто указать путь относительно MEDIA_ROOT
                    'icon': sport_data.get('icon_path') if sport_data.get('icon_path') else None
                }
            )
            created_sport_types[sport_data['name']] = sport_type_obj
        self.stdout.write(self.style.SUCCESS('Виды спорта созданы/обновлены.'))

        # --- 3. Типы мероприятий ---
        self.stdout.write('Создание типов мероприятий...')
        event_types_data = [
            {'name': 'Турнир', 'description': 'Соревнование с выбыванием или круговой системой'},
            {'name': 'Товарищеский матч', 'description': 'Встреча команд без призов и званий'},
            {'name': 'Тренировка', 'description': 'Общая тренировка для улучшения навыков'},
            {'name': 'Мастер-класс', 'description': 'Демонстрация и обучение от эксперта'},
            {'name': 'Чемпионат', 'description': 'Официальное соревнование высокого уровня'},
            {'name': 'Фестиваль', 'description': 'Массовое спортивное мероприятие'},
            {'name': 'Забег', 'description': 'Организованное соревнование по бегу'},
            {'name': 'Марафон', 'description': 'Забег на дистанцию 42.195 км'},
            {'name': 'Онлайн-турнир', 'description': 'Соревнование, проводимое через интернет'},
            {'name': 'Сбор для игры', 'description': 'Неформальный сбор для совместной игры'},
        ]

        created_event_types = {}
        for event_data in event_types_data:
            event_type, created = EventType.objects.get_or_create(
                name=event_data['name'],
                defaults={'description': event_data['description']}
            )
            created_event_types[event_data['name']] = event_type
        self.stdout.write(self.style.SUCCESS('Типы мероприятий созданы/обновлены.'))

        # --- 4. Локации ---
        self.stdout.write('Создание локаций...')
        location1, _ = Location.objects.get_or_create(
            name='Стадион "Лужники"',
            address='Лужнецкая наб., 24',
            city='Москва',
            defaults={
                'latitude': 55.715752,
                'longitude': 37.553701,
                'details': 'Главная спортивная арена России. Вход со стороны набережной.',
                'created_by_user': admin_user
            }
        )
        location2, _ = Location.objects.get_or_create(
            name='Парк "Сокольники"',
            address='ул. Сокольнический Вал, 1, стр. 1',
            city='Москва',
            defaults={
                'latitude': 55.794839,
                'longitude': 37.676271,
                'details': 'Место для пробежек и уличных тренировок. Сбор у главного входа.',
                'created_by_user': user_ivan
            }
        )
        location3, _ = Location.objects.get_or_create(
            name='Спортзал "Атлант"',
            address='ул. Ленина, 15',
            city='Екатеринбург',
            defaults={
                'details': 'Уютный зал для баскетбола и волейбола.',
                'created_by_user': user_maria
            }
        )
        location4, _ = Location.objects.get_or_create(
            name='Компьютерный клуб "Respawn"',
            address='ул. Киберспортсменов, 1',
            city='Санкт-Петербург',
            defaults={
                'details': 'Современный клуб с мощным железом. Турнирная зона на 2-м этаже.',
                'created_by_user': user_alex
            }
        )
        self.stdout.write(self.style.SUCCESS('Локации созданы/получены.'))

        # --- 5. Мероприятия ---
        self.stdout.write('Создание мероприятий...')
        now = timezone.now()

        event1, _ = Event.objects.get_or_create(
            title='Весенний футбольный турнир "Надежда"',
            organizer=user_ivan,
            sport_type=created_sport_types['Футбол'],
            event_type=created_event_types['Турнир'],
            defaults={
                'description': 'Ежегодный турнир для любительских команд. Приглашаем всех желающих! Команды 5х5.',
                'location': location1,
                'start_datetime': now + timedelta(days=30, hours=2),  # через 30 дней в 14:00 (если now = 12:00)
                'end_datetime': now + timedelta(days=30, hours=6),
                'registration_deadline': now + timedelta(days=25),
                'max_participants': 16,  # команд
                'status': 'REGISTRATION_OPEN',
                'is_public': True,
                'entry_fee': 500.00,
                'contact_email': user_ivan.email,
                'contact_phone': '+79001234567'
            }
        )

        event2, _ = Event.objects.get_or_create(
            title='Утренняя йога в парке Сокольники',
            organizer=user_maria,
            sport_type=created_sport_types['Йога'],
            event_type=created_event_types['Тренировка'],
            defaults={
                'description': 'Зарядись энергией на весь день! Практика для всех уровней подготовки. Коврик с собой.',
                'location': location2,
                'start_datetime': now + timedelta(days=7, hours=-2),  # через 7 дней в 10:00
                'end_datetime': now + timedelta(days=7, hours=-1),  # до 11:00
                'status': 'REGISTRATION_OPEN',
                'is_public': True,
                'entry_fee': None,  # Бесплатно
                'contact_email': user_maria.email,
            }
        )

        event3, _ = Event.objects.get_or_create(
            title='Товарищеский матч по баскетболу (Друзья)',
            organizer=user_oleg,
            sport_type=created_sport_types['Баскетбол'],
            event_type=created_event_types['Товарищеский матч'],
            defaults={
                'description': 'Собираемся поиграть в баскетбол своей компанией. Место: школьный двор на ул. Мира, 5.',
                'custom_location_text': 'Школьный двор на ул. Мира, 5, г. Екатеринбург',
                'start_datetime': now + timedelta(days=2, hours=5),  # через 2 дня в 17:00
                'max_participants': 10,
                'status': 'REGISTRATION_OPEN',
                'is_public': False,  # Приватное мероприятие
                'contact_phone': user_oleg.email.split('@')[0]  # Просто для примера
            }
        )

        event4, _ = Event.objects.get_or_create(
            title='Чемпионат города по шахматам "Белая Ладья"',
            organizer=admin_user,  # Администратор тоже может быть организатором
            sport_type=created_sport_types['Шахматы'],
            event_type=created_event_types['Чемпионат'],
            defaults={
                'description': 'Главный шахматный турнир города. Определение чемпиона и призеров. Swiss system, 9 туров.',
                'location': location3,  # Допустим, в спортзале есть конференц-зал
                'start_datetime': now - timedelta(days=10),  # Прошло 10 дней назад
                'end_datetime': now - timedelta(days=8),
                'registration_deadline': now - timedelta(days=15),
                'max_participants': 64,
                'current_participants_count': 58,  # Предположим, столько было
                'status': 'COMPLETED',
                'is_public': True,
                'entry_fee': 200.00,
                'contact_email': admin_user.email,
            }
        )

        event5, _ = Event.objects.get_or_create(
            title='Онлайн-турнир по Dota 2 "Weekend Cup"',
            organizer=user_alex,
            sport_type=created_sport_types['Киберспорт'],
            event_type=created_event_types['Онлайн-турнир'],
            defaults={
                'description': 'Еженедельный онлайн-турнир для всех желающих. Призовой фонд! Регистрация на нашем Discord сервере.',
                'custom_location_text': 'Онлайн (Discord: dsc.gg/weekendcup)',
                'start_datetime': now + timedelta(days=5, hours=6),  # Через 5 дней в 18:00
                'registration_deadline': now + timedelta(days=4),
                'max_participants': 32,  # Команд
                'status': 'REGISTRATION_OPEN',
                'is_public': True,
                'entry_fee': 100.00,
                'contact_email': user_alex.email,
            }
        )

        event6, _ = Event.objects.get_or_create(
            title='Сбор на падел-теннис для начинающих',
            organizer=user_ivan,
            sport_type=created_sport_types['Падел-теннис'],
            event_type=created_event_types['Сбор для игры'],
            defaults={
                'description': 'Ищем компанию для игры в падел. Уровень: начинающие и чуть выше. Аренда корта пополам.',
                'location': location3,  # Предположим, там есть и падел-корты
                'start_datetime': now + timedelta(days=3, hours=7),  # Через 3 дня в 19:00
                'max_participants': 4,
                'status': 'PLANNED',
                'is_public': True,
                'contact_email': user_ivan.email,
            }
        )
        self.stdout.write(self.style.SUCCESS('Мероприятия созданы/получены.'))

        # --- 6. Регистрации на мероприятия ---
        self.stdout.write('Создание регистраций на мероприятия...')

        # Регистрации на Футбольный турнир (event1)
        reg1, created = EventRegistration.objects.get_or_create(
            event=event1, user=user_maria,
            defaults={'status': 'CONFIRMED', 'notes_by_user': 'Капитан команды "Ракета"'}
        )
        if created:
            event1.current_participants_count = EventRegistration.objects.filter(event=event1, status='CONFIRMED').count()
            event1.save()

        reg2, created = EventRegistration.objects.get_or_create(
            event=event1, user=user_oleg,
            defaults={'status': 'PENDING_APPROVAL', 'notes_by_user': 'Готов играть! Команда "Молния"'}
        )

        # Регистрации на Йогу (event2)
        reg3, created = EventRegistration.objects.get_or_create(
            event=event2, user=user_ivan,  # Организатор тоже может "зарегистрироваться" для учета
            defaults={'status': 'CONFIRMED'}
        )
        if created:
            event2.current_participants_count = EventRegistration.objects.filter(event=event2, status='CONFIRMED').count()
            event2.save()

        reg4, created = EventRegistration.objects.get_or_create(
            event=event2, user=user_oleg,
            defaults={'status': 'CONFIRMED'}
        )
        if created:
            event2.current_participants_count = EventRegistration.objects.filter(event=event2, status='CONFIRMED').count()
            event2.save()

        # Регистрации на Онлайн-турнир (event5)
        reg5, created = EventRegistration.objects.get_or_create(
            event=event5, user=user_ivan,  # Иван решил попробовать себя в киберспорте
            defaults={'status': 'CONFIRMED', 'notes_by_user': 'Team "OldSchoolGamers"'}
        )
        if created:
            event5.current_participants_count = EventRegistration.objects.filter(event=event5, status='CONFIRMED').count()
            event5.save()

        reg6, created = EventRegistration.objects.get_or_create(
            event=event5, user=user_maria,  # Мария тоже
            defaults={'status': 'PENDING_APPROVAL', 'notes_by_user': 'Team "Newbies", нужен +1'}
        )

        self.stdout.write(self.style.SUCCESS('Регистрации созданы/получены.'))

        # --- 7. Результаты мероприятий (для завершенных) ---
        self.stdout.write('Создание результатов для завершенных мероприятий...')

        # Результаты для Чемпионата по шахматам (event4)
        # Предположим, Алексей и Мария участвовали и были зарегистрированы (для простоты не создаем регистрации)
        EventResult.objects.get_or_create(
            event=event4,
            participant_user=user_alex,
            recorded_by_user=admin_user,
            defaults={
                'position': 1,
                'score': '8.5/9',
                'achievement_description': 'Чемпион города!'
            }
        )
        EventResult.objects.get_or_create(
            event=event4,
            participant_user=user_maria,
            recorded_by_user=admin_user,
            defaults={
                'position': 3,
                'score': '7/9',
                'achievement_description': 'Бронзовый призер'
            }
        )
        EventResult.objects.get_or_create(
            event=event4,
            team_name_if_applicable='Зарегистрированный_Участник_Без_Аккаунта_Петров',
            # Если участник не был User в системе
            recorded_by_user=admin_user,
            defaults={
                'position': 10,
                'score': '5/9',
            }
        )
        self.stdout.write(self.style.SUCCESS('Результаты созданы/получены.'))

        self.stdout.write(self.style.SUCCESS('Все начальные данные успешно загружены!'))