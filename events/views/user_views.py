from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from ..serializers import UserSerializer

User = get_user_model()


class UserProfileView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)

        # Пароль требует специальной обработки
        if 'password' in request.data:
            old_password = request.data.get('old_password')
            if not old_password or not user.check_password(old_password):
                return Response({'error': 'Необходимо указать текущий пароль'},
                                status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            # Если меняем email, проверяем его уникальность
            if 'email' in serializer.validated_data and serializer.validated_data['email'] != user.email:
                if User.objects.filter(email=serializer.validated_data['email']).exists():
                    return Response({'error': 'Этот email уже используется'},
                                    status=status.HTTP_400_BAD_REQUEST)

            # Обрабатываем пароль отдельно
            if 'password' in serializer.validated_data:
                user.set_password(serializer.validated_data.pop('password'))

            # Сохраняем остальные поля
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)