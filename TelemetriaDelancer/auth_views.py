import secrets

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class LoginView(APIView):
    """
    Autenticación por usuario/contraseña de Django.
    Los endpoints de telemetría actuales no validan el Bearer; el token sirve para el frontend.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        if not username or not password:
            return Response(
                {'detail': 'Usuario y contraseña son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Credenciales inválidas. Verifica tu usuario y contraseña.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token = secrets.token_urlsafe(48)
        return Response(
            {
                'token': token,
                'user': {
                    'id': user.id,
                    'email': user.email or '',
                    'name': user.get_full_name() or user.username,
                    'role': 'admin' if user.is_superuser else 'user',
                },
            }
        )
