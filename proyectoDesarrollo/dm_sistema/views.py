# ./dm_sistema/views.py
from __future__ import annotations

import crypt
import secrets
import jwt
import requests                       # ← añadimos import
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Operador, Sesiones, SesionesActivas
from .serializer import OperadorLoginSerializer


# ------------------------------------------------------------------------- #
# Función auxiliar para enviar correos usando el micro-servicio legado      #
# ------------------------------------------------------------------------- #
def enviar_correo_python(
    remitente: str,
    correo_destino: str,
    asunto: str,
    detalle: str,
) -> None:
    """Consume el micro-servicio PHP legado que envía correos."""
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

    # --------------------------------------------------------------------- #
    # Helpers                                                               #
    # --------------------------------------------------------------------- #
    @staticmethod
    def _get_client_ip(request) -> str:
        """Obtiene la IP real del cliente, incluso detrás de proxies/Nginx."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # X-Forwarded-For puede traer una lista de IPs → tomamos la primera
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    # --------------------------------------------------------------------- #
    # POST                                                                  #
    # --------------------------------------------------------------------- #
    def post(self, request, *args, **kwargs):
        serializer = OperadorLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        # ------------------------------------------------------------------ #
        # 1. Verificamos credenciales                                        #
        # ------------------------------------------------------------------ #
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

        # ------------------------------------------------------------------ #
        # 2. Credenciales correctas → registramos sesión + sesión activa     #
        # ------------------------------------------------------------------ #
        client_ip = self._get_client_ip(request)

        # Generamos token JWT y código de verificación aleatorio
        token_payload = {
            "sub": operador.id,                                      # sujeto = operador
            "iat": int(datetime.now(dt_timezone.utc).timestamp()),   # issued-at
            "jti": secrets.token_hex(8),                             # ID único
        }
        jwt_token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")
        cod_verificacion = secrets.token_hex(16)  # hash aleatorio

        with transaction.atomic():
            # Insertamos registro en dm_sistema.sesiones
            sesion = Sesiones.objects.create(
                ip=client_ip,
                fecha=timezone.now(),
                id_operador=operador,
                id_empresa=operador.id_empresa,
            )

            # Insertamos registro en dm_sistema.sesiones_activas
            SesionesActivas.objects.create(
                id_empresa=operador.id_empresa,
                id_operador=operador,
                id_sesion=sesion,                # FK → sesión recién creada
                fecha_registro=timezone.now(),
                token=jwt_token,
                cod_verificacion=cod_verificacion,
            )

        # ------------------------------------------------------------------ #
        # 3. Enviamos el código de verificación al correo del usuario        #
        # ------------------------------------------------------------------ #
        enviar_correo_python(
            "DM",
            operador.username,                       # el username es el correo
            "Código de Verificación",
            f"Hola, tu código es: {cod_verificacion}",
        )

        # ------------------------------------------------------------------ #
        # 4. Respondemos al cliente                                          #
        # ------------------------------------------------------------------ #
        return Response(
            {
                "detail": "Credenciales válidas",
                "token": jwt_token,
                "cod_verificacion": cod_verificacion,
            },
            status=status.HTTP_200_OK,
        )
