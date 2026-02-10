import os
import requests
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from users.serializers import OAuthCodeSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()

class GoogleLoginAPIView(CreateAPIView):
    serializer_class = OAuthCodeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # OAuth-код от Google
        code = serializer.validated_data['code']

        # Меняем code на access_token
        token_response = requests.post(
            url="https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": os.environ.get('CLIENT_ID'),
                "client_secret": os.environ.get('CLIENT_SECRET'),
                "redirect_uri": "http://localhost:8000/api/v1/users/google-login/",
                "grant_type": "authorization_code"
            }
        )

        token_data  = token_response.json() # Преобразуем в JSON
        access_token = token_data.get('access_token') # Получаем access_token

        # Если Google не вернул токен
        if not access_token:
            return Response({"error": "Invalid token!"})

        # Получаем данные пользователя от Google
        user_info = requests.get(
            url="https://www.googleapis.com/oauth2/v3/userinfo",
            params={"alt": "json"}, # Указываем формат ответа JSON
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        email = user_info['email'] # Получаем email пользователя
        family_name = user_info.get('family_name', '')
        given_name = user_info.get('given_name', '')

        # Создаём пользователя или берём существующего на основе email
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': given_name,
                'last_name': family_name,
                'is_active': True,
                "registration_source": "google",
            })

        if not user.registration_source:
            user.registration_source = "google"

        user.last_login = timezone.now()
        user.save()

        # Генерируем JWT токены
        refresh = RefreshToken.for_user(user)
        refresh['email'] = user.email # Добавляем email в payload токена

        # Возвращаем токены
        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        })