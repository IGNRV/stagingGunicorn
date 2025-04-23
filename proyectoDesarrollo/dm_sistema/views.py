# ./dm_sistema/views.py

from __future__ import annotations

import crypt
import jwt
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Operador,
    Sesiones,
    SesionesActivas,
)
from .serializer import OperadorLoginSerializer


def _get_client_ip(request) -> str:
    """Obtiene la IP real detrás de un proxy (si existe)."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # El primer valor es la IP del cliente
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class OperadorLoginAPIView(APIView):
    """
    POST /dm_sistema/operadores/validar/

    Body JSON:
    {
        "username": "usuario",
        "password": "secreto"
    }
    """
    authentication_classes: list = []  # ruta pública
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        serializer = OperadorLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            operador = Operador.objects.get(username=username)
        except Operador.DoesNotExist:
            return Response(
                {"detail": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        password_hash = operador.password or ""
        if not (password_hash and crypt.crypt(password, password_hash) == password_hash):
            return Response(
                {"detail": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ---------------------------------------------------------------------
        # 1) Insertar registro en dm_sistema.sesiones
        # ---------------------------------------------------------------------
        ahora = timezone.now()
        ip_cliente = _get_client_ip(request)

        sesion = Sesiones.objects.create(
            ip=ip_cliente,
            fecha=ahora,
            id_operador=operador,
            id_empresa=operador.id_empresa,
        )

        # ---------------------------------------------------------------------
        # 2) Generar token JWT y código de verificación
        # ---------------------------------------------------------------------
        payload = {
            "sub": operador.id,
            "iat": int(ahora.timestamp()),
            "exp": int((ahora + timedelta(hours=8)).timestamp()),
        }
        token_jwt: str = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        cod_verificacion: str = secrets.token_hex(16)

        # ---------------------------------------------------------------------
        # 3) Insertar registro en dm_sistema.sesiones_activas
        # ---------------------------------------------------------------------
        SesionesActivas.objects.create(
            id_empresa=operador.id_empresa,
            id_operador=operador,
            id_sesion=sesion,
            fecha_registro=ahora,
            token=token_jwt,
            cod_verificacion=cod_verificacion,
        )

        # ---------------------------------------------------------------------
        # 4) Respuesta
        # ---------------------------------------------------------------------
        return Response(
            {
                "detail": "Credenciales válidas",
                "token": token_jwt,            # opcional: se devuelve para uso del frontend
                "cod_verificacion": cod_verificacion,
            },
            status=status.HTTP_200_OK,
        )
