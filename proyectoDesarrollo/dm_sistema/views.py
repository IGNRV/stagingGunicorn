# ./dm_sistema/views.py
from __future__ import annotations

import crypt
import secrets
import jwt
import requests
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Operador, Sesiones, SesionesActivas
from .serializer import (
    OperadorLoginSerializer,
    OperadorVerificarSerializer,
)

# ------------------------------------------------------------------------- #
# Función auxiliar para enviar correos                                       #
# ------------------------------------------------------------------------- #
def enviar_correo_python(
    remitente: str,
    correo_destino: str,
    asunto: str,
    detalle: str,
) -> None:
    try:
        requests.post(
            "http://mail.smartgest.cl/mailserver/server_mail.php",
            data={
                "destino": correo_destino,
                "asunto":  asunto,
                "detalle": detalle,
                "from":    remitente,
            },
            timeout=8,
        )
    except Exception as exc:                 # pragma: no cover
        print(f"[WARN] Falló el envío de correo: {exc}")


# ------------------------------------------------------------------------- #
#  LOGIN / VALIDAR                                                           #
# ------------------------------------------------------------------------- #
class OperadorLoginAPIView(APIView):
    authentication_classes: list = []
    permission_classes:     list = []

    @staticmethod
    def _get_client_ip(request) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "")

    def post(self, request, *args, **kwargs):
        serializer = OperadorLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            op = Operador.objects.get(username=username)
        except Operador.DoesNotExist:
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        if crypt.crypt(password, op.password or "") != (op.password or ""):
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        client_ip = self._get_client_ip(request)

        token_payload = {
            "sub": op.id,
            "iat": int(datetime.now(dt_timezone.utc).timestamp()),
            "jti": secrets.token_hex(8),
        }
        jwt_token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")
        cod_verificacion = secrets.token_hex(16)

        with transaction.atomic():
            sesion = Sesiones.objects.create(
                ip=client_ip,
                fecha=timezone.now(),
                id_operador=op,
                id_empresa=op.id_empresa,
            )
            SesionesActivas.objects.create(
                id_empresa=op.id_empresa,
                id_operador=op,
                id_sesion=sesion,
                fecha_registro=timezone.now(),
                token=jwt_token,
                cod_verificacion=cod_verificacion,
            )

        enviar_correo_python(
            "DM",
            op.username,
            "Código de Verificación",
            f"Hola, tu código es: {cod_verificacion}",
        )

        return Response(
            {
                "detail": "Credenciales válidas",
                "token": jwt_token,
                "cod_verificacion": cod_verificacion,
            },
            status=status.HTTP_200_OK,
        )


# ------------------------------------------------------------------------- #
#  VERIFICAR CÓDIGO                                                          #
# ------------------------------------------------------------------------- #
class OperadorCodigoVerificacionAPIView(APIView):
    """
    POST /dm_sistema/operadores/verificar/

    Body:
    {
        "username": "",
        "cod_verificacion": ""
    }
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        serializer = OperadorVerificarSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        codigo   = serializer.validated_data["cod_verificacion"]

        try:
            op = Operador.objects.get(username=username)
        except Operador.DoesNotExist:
            return Response({"detail": "Usuario o código inválido"}, status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .filter(id_operador=op, cod_verificacion=codigo)
            .order_by("-fecha_registro")
            .first()
        )

        if not sesion_activa:
            return Response({"detail": "Usuario o código inválido"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            {
                "detail": "Código verificado correctamente",
                "token":  sesion_activa.token,
            },
            status=status.HTTP_200_OK,
        )
