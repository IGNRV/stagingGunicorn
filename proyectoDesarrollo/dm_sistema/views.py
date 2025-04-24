# ./dm_sistema/views.py
from __future__ import annotations

import crypt
import secrets
import jwt
import requests
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.db import transaction, connection
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from dm_logistica.models import Proveedor, Giro
from .models import Operador, Sesiones, SesionesActivas
from .serializer import (
    OperadorLoginSerializer,
    OperadorVerificarSerializer,
    OperadorSerializer,
    ProveedorSerializer,
    GiroSerializer,
)

# ------------------------------------------------------------------------- #
#  CONSTANTES SQL – SE COMPARTEN ENTRE LOS ENDPOINTS                        #
# ------------------------------------------------------------------------- #
QUERY_MODULOS = """
    SELECT c.nombre_menu,
           b.id_modulo,
           c.icon
      FROM dm_sistema.operador_empresa_modulos     a
INNER JOIN dm_sistema.empresa_modulo           b
        ON a.id_empresa_modulo = b.id_modulo
INNER JOIN dm_sistema.modulos                   c
        ON b.id_modulo         = c.id
     WHERE a.id_operador = %s
       AND b.estado      = 1
       AND c.estado      = 1
       AND b.id_empresa  = %s
  ORDER BY c.orden
"""

QUERY_FUNCIONALIDADES = """
    SELECT m.id, m.url, m.texto, m.etiqueta, m.descripcion,
           m.nivel_menu, m.orden, m.modificable, m.separador_up,
           m.id_modulo
      FROM dm_sistema.operador                        o
INNER JOIN dm_sistema.operador_empresa_modulos_menu oemm
        ON o.id                   = oemm.id_operador
INNER JOIN dm_sistema.empresa_modulos_menu          emm
        ON oemm.id_empresa_modulos_menu = emm.id_empresa_modulo
INNER JOIN dm_sistema.menus                        m
        ON emm.id_menu              = m.id
     WHERE o.id = %s
"""

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
#  HELPER → arma operador/modulos/funcionalidades/proveedores/giros         #
# ------------------------------------------------------------------------- #
def build_payload(operador: Operador) -> dict:
    """
    Devuelve un diccionario con:
        • operador
        • modulos
        • funcionalidades
        • proveedores
        • giros
    """
    operador_dict = OperadorSerializer(operador).data

    with connection.cursor() as cursor:
        # -------------------------- MÓDULOS ------------------------------ #
        cursor.execute(QUERY_MODULOS, [operador.id, operador.id_empresa_id])
        mod_rows = cursor.fetchall()
        modulos = [
            {
                "nombre_menu": row[0],
                "id_modulo":   row[1],
                "icon":        row[2],
            }
            for row in mod_rows
        ]

        # ----------------------- FUNCIONALIDADES ------------------------- #
        cursor.execute(QUERY_FUNCIONALIDADES, [operador.id])
        func_rows = cursor.fetchall()
        funcionalidades = [
            {
                "id":            row[0],
                "url":           row[1],
                "texto":         row[2],
                "etiqueta":      row[3],
                "descripcion":   row[4],
                "nivel_menu":    row[5],
                "orden":         row[6],
                "modificable":   row[7],
                "separador_up":  row[8],
                "id_modulo":     row[9],
            }
            for row in func_rows
        ]

    # --------------------------- PROVEEDORES ----------------------------- #
    proveedores_qs   = Proveedor.objects.filter(id_empresa=operador.id_empresa_id)
    proveedores_data = ProveedorSerializer(proveedores_qs, many=True).data

    # ------------------------------ GIROS -------------------------------- #
    giros_qs   = Giro.objects.filter(id_empresa=operador.id_empresa_id)
    giros_data = GiroSerializer(giros_qs, many=True).data

    return {
        "operador":        operador_dict,
        "modulos":         modulos,
        "funcionalidades": funcionalidades,
        "proveedores":     proveedores_data,
        "giros":           giros_data,
    }


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

        # ------------------------------------------------------------------ #
        # 1. Verificamos credenciales                                        #
        # ------------------------------------------------------------------ #
        try:
            op = Operador.objects.select_related("id_empresa").get(username=username)
        except Operador.DoesNotExist:
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        if crypt.crypt(password, op.password or "") != (op.password or ""):
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        # ------------------------------------------------------------------ #
        # 1.1  Empresa activa? (estado = 1)                                  #
        # ------------------------------------------------------------------ #
        empresa = op.id_empresa                         # FK → dm_sistema.empresa
        if not empresa or empresa.estado != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ------------------------------------------------------------------ #
        # 2. Credenciales correctas → registramos sesión + sesión activa     #
        # ------------------------------------------------------------------ #
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
                id_empresa=empresa,
            )
            SesionesActivas.objects.create(
                id_empresa=empresa,
                id_operador=op,
                id_sesion=sesion,
                fecha_registro=timezone.now(),
                token=jwt_token,
                cod_verificacion=cod_verificacion,
            )

        # ------------------------------------------------------------------ #
        # 3. Enviamos el código de verificación al correo del usuario        #
        # ------------------------------------------------------------------ #
        enviar_correo_python(
            "DM",
            op.username,
            "Código de Verificación",
            f"Hola, tu código es: {cod_verificacion}",
        )

        # ------------------------------------------------------------------ #
        # 4. Respondemos al cliente + Cookie con el token                    #
        # ------------------------------------------------------------------ #
        response = Response(
            {"detail": "Credenciales válidas"},
            status=status.HTTP_200_OK,
        )
        response.set_cookie(
            key="auth_token",
            value=jwt_token,
            httponly=True,
            secure=True,        # Ajusta a False si no usas HTTPS
            samesite="Lax",
            max_age=60 * 60 * 24,   # 1 día
        )
        return response


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
            op = Operador.objects.select_related("id_empresa").get(username=username)
        except Operador.DoesNotExist:
            return Response({"detail": "Usuario o código inválido"}, status=status.HTTP_401_UNAUTHORIZED)

        # ------------------------------------------------------------------ #
        # 0. Empresa activa?                                                 #
        # ------------------------------------------------------------------ #
        if not op.id_empresa or op.id_empresa.estado != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        sesion_activa = (
            SesionesActivas.objects
            .filter(id_operador=op, cod_verificacion=codigo)
            .order_by("-fecha_registro")
            .first()
        )

        if not sesion_activa:
            return Response({"detail": "Usuario o código inválido"}, status=status.HTTP_401_UNAUTHORIZED)

        # ------------------------------------------------------------------ #
        # Eliminamos todas las otras sesiones activas                        #
        # ------------------------------------------------------------------ #
        with transaction.atomic():
            (SesionesActivas.objects
                .filter(id_operador=op)
                .exclude(pk=sesion_activa.pk)
                .delete())

        # ------------------------------------------------------------------ #
        # Construimos la respuesta                                           #
        # ------------------------------------------------------------------ #
        payload = build_payload(op)

        return Response(payload, status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  OBTENER OPERADOR, MÓDULOS, FUNCIONALIDADES, PROVEEDORES Y GIROS POR TOKEN#
# ------------------------------------------------------------------------- #
class OperadorSesionActivaTokenAPIView(APIView):
    """
    GET /dm_sistema/operadores/sesiones-activas-token/

    Devuelve:
    {
        "operador": { ... },
        "modulos":  [ ... ],
        "funcionalidades": [ ... ],
        "proveedores": [ ... ],
        "giros": [ ... ]
    }
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def get(self, request, *args, **kwargs):
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response(
                {"detail": "Token no proporcionado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response(
                {"detail": "Token inválido o sesión expirada"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ------------------------------------------------------------------ #
        # Empresa sigue activa?                                              #
        # ------------------------------------------------------------------ #
        if not sesion_activa.id_operador.id_empresa or sesion_activa.id_operador.id_empresa.estado != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        respuesta = build_payload(sesion_activa.id_operador)
        return Response(respuesta, status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  LOGOUT – elimina la sesión activa referida por la cookie                 #
# ------------------------------------------------------------------------- #
class OperadorLogoutAPIView(APIView):
    """
    GET /dm_sistema/operadores/logout/

    • El cliente debe enviar la cookie `auth_token`.
    • Se elimina la fila correspondiente en dm_sistema.sesiones_activas.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def get(self, request, *args, **kwargs):
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response(
                {"detail": "Token no proporcionado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        SesionesActivas.objects.filter(token=token_cookie).delete()

        response = Response(
            {"detail": "Sesión cerrada correctamente"},
            status=status.HTTP_200_OK,
        )
        response.set_cookie(
            key="auth_token",
            value="",
            max_age=0,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        return response
