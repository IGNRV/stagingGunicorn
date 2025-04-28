# --------------------------------------------------------------------------- #
# ./dm_sistema/views.py                                                       #
# --------------------------------------------------------------------------- #
from __future__ import annotations

import crypt
import secrets
import jwt
import requests
from datetime import datetime, timezone as dt_timezone
from typing import Any, Dict

from django.conf import settings
from django.db import transaction, connection
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# ------------------------------------------------------------------ #
# MODELOS Y SERIALIZERS                                              #
# ------------------------------------------------------------------ #
from dm_logistica.models import (
    Proveedor,          # crear / listar / obtener / editar proveedor
    Bodega,             # crear / listar / obtener / editar bodegas
    BodegaTipo,         # listar / obtener tipos de bodega
)
from .models import Operador, Sesiones, SesionesActivas, Comuna, Region
from .serializer import (
    OperadorLoginSerializer,
    OperadorVerificarSerializer,
    OperadorSerializer,
    ProveedorSerializer,
    BodegaSerializer,
    BodegaTipoSerializer,
    ComunaSerializer,
    RegionSerializer,
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
#  UTILIDAD → ENVÍO DE CORREOS                                              #
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
#  HELPERs                                                                   #
# ------------------------------------------------------------------------- #
def build_payload(operador: Operador) -> dict:
    """Devuelve operador + módulos + funcionalidades (sin bodegas)."""
    operador_dict = OperadorSerializer(operador).data

    with connection.cursor() as cursor:
        cursor.execute(QUERY_MODULOS, [operador.id, operador.id_empresa_id])
        modulos = [
            {"nombre_menu": row[0], "id_modulo": row[1], "icon": row[2]}
            for row in cursor.fetchall()
        ]

        cursor.execute(QUERY_FUNCIONALIDADES, [operador.id])
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
            for row in cursor.fetchall()
        ]

    return {
        "operador":        operador_dict,
        "modulos":         modulos,
        "funcionalidades": funcionalidades,
    }


def _normalize_request_data(data: Any) -> Dict[str, Any]:
    """
    Convierte cualquier `QueryDict` / `OrderedDict` en un `dict` plano
    tomando solo el primer valor cuando sea lista.
    """
    if hasattr(data, "items"):                 # QueryDict / OrderedDict
        data_dict = {k: v for k, v in data.items()}
    else:
        data_dict = dict(data)

    for k, v in data_dict.items():             # deslistar valores
        if isinstance(v, list) and v:
            data_dict[k] = v[0]

    return data_dict


# ------------------------------------------------------------------------- #
#  LOGIN / VALIDAR                                                          #
# ------------------------------------------------------------------------- #
class OperadorLoginAPIView(APIView):
    """
    POST /dm_sistema/operadores/validar/

    • Comprueba usuario y contraseña.
    • Si `operador_verificacion` == 1:
          - registra la sesión,
          - envía un código de verificación por correo,
          - **no** entrega la cookie hasta que se valide el código.
      Si `operador_verificacion` == 0:
          - registra la sesión,
          - **no** envía código,
          - entrega inmediatamente la cookie con el token **y**
            actualiza `operador_verificacion` a 1.
    """
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

        # ---------------------- 1. Credenciales ------------------------- #
        try:
            op = (
                Operador
                .objects
                .select_related("id_empresa")
                .get(username=username)
            )
        except Operador.DoesNotExist:
            return Response({"detail": "Credenciales inválidas"},
                            status=status.HTTP_401_UNAUTHORIZED)

        if crypt.crypt(password, op.password or "") != (op.password or ""):
            return Response({"detail": "Credenciales inválidas"},
                            status=status.HTTP_401_UNAUTHORIZED)

        # ---------------------- 2. Empresa activa ----------------------- #
        empresa = op.id_empresa
        if not empresa or empresa.estado != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ---------------------- 3. Registramos sesión ------------------- #
        client_ip = self._get_client_ip(request)
        token_payload = {
            "sub": op.id,
            "iat": int(datetime.now(dt_timezone.utc).timestamp()),
            "jti": secrets.token_hex(8),
        }
        jwt_token        = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")
        cod_verificacion = secrets.token_hex(3)  # 6 caracteres hex

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

            # ------------ 3.a  Flujo sin verificación (operador_verificacion == 0) ---- #
            if (op.operador_verificacion or 0) == 0:
                #   – Marcamos el operador como verificado para próximas sesiones
                op.operador_verificacion = 1
                op.save(update_fields=["operador_verificacion"])

                #   – Armamos el payload completo
                payload  = build_payload(op)

                #   – Respondemos con cookie inmediatamente
                response = Response(payload, status=status.HTTP_200_OK)
                response.set_cookie(
                    key="auth_token",
                    value=jwt_token,
                    httponly=True,
                    secure=True,
                    samesite="Lax",
                    max_age=60 * 60 * 24,      # 24 h
                )
                return response        # ← fin del flujo sin verificación

        # ---------------------- 4. Flujo con verificación (valor = 1) ---- #
        enviar_correo_python(
            "DM",
            op.username,
            "Código de Verificación",
            f"Hola, tu código es: {cod_verificacion}",
        )

        return Response(
            {
                "detail": (
                    "Credenciales válidas. "
                    "Revisa tu correo e ingresa el código de verificación."
                )
            },
            status=status.HTTP_200_OK,
        )


# ------------------------------------------------------------------------- #
#  VERIFICAR CÓDIGO                                                         #
# ------------------------------------------------------------------------- #
class OperadorCodigoVerificacionAPIView(APIView):
    """
    POST /dm_sistema/operadores/verificar/

    Body:
    {
        "username": "",
        "cod_verificacion": ""
    }

    • Si el código es correcto, elimina otras sesiones activas del usuario,
      entrega la cookie `auth_token` y devuelve el payload completo.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        serializer = OperadorVerificarSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        codigo   = serializer.validated_data["cod_verificacion"]

        # ------------------ 1. Usuario existente ------------------------ #
        try:
            op = Operador.objects.select_related("id_empresa").get(username=username)
        except Operador.DoesNotExist:
            return Response({"detail": "Usuario o código inválido"},
                            status=status.HTTP_401_UNAUTHORIZED)

        # ------------------ 2. Empresa activa --------------------------- #
        if not op.id_empresa or op.id_empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ------------------ 3. Código coincide -------------------------- #
        sesion_activa = (
            SesionesActivas.objects
            .filter(id_operador=op, cod_verificacion=codigo)
            .order_by("-fecha_registro")
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Usuario o código inválido"},
                            status=status.HTTP_401_UNAUTHORIZED)

        # ------------------ 4. Invalidamos otras sesiones --------------- #
        with transaction.atomic():
            (SesionesActivas.objects
                .filter(id_operador=op)
                .exclude(pk=sesion_activa.pk)
                .delete())

        # ------------------ 5. Respondemos + cookie --------------------- #
        payload  = build_payload(op)
        response = Response(payload, status=status.HTTP_200_OK)
        response.set_cookie(
            key="auth_token",
            value=sesion_activa.token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=60 * 60 * 24,
        )
        return response


# ------------------------------------------------------------------------- #
#  OBTENER OPERADOR / MÓDULOS / FUNCIONALIDADES POR TOKEN                   #
# ------------------------------------------------------------------------- #
class OperadorSesionActivaTokenAPIView(APIView):
    """
    GET /dm_sistema/operadores/sesiones-activas-token/
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def get(self, request, *args, **kwargs):
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not sesion_activa.id_operador.id_empresa or sesion_activa.id_operador.id_empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        return Response(build_payload(sesion_activa.id_operador),
                        status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  LOGOUT                                                                   #
# ------------------------------------------------------------------------- #
class OperadorLogoutAPIView(APIView):
    """
    GET /dm_sistema/operadores/logout/

    • Elimina la fila en `dm_sistema.sesiones_activas` asociada al token
      de la cookie y limpia la cookie en el navegador.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def get(self, request, *args, **kwargs):
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        SesionesActivas.objects.filter(token=token_cookie).delete()

        response = Response({"detail": "Sesión cerrada correctamente"},
                            status=status.HTTP_200_OK)
        response.set_cookie(
            key="auth_token",
            value="",
            max_age=0,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        return response


# ------------------------------------------------------------------------- #
#  LISTAR PROVEEDORES POR EMPRESA                                           #
# ------------------------------------------------------------------------- #
class ProveedorListAPIView(APIView):
    """
    GET /dm_sistema/logistica/proveedores/
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def get(self, request, *args, **kwargs):
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        qs = Proveedor.objects.filter(id_empresa=empresa.id).order_by("nombre_rs")
        return Response(ProveedorSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  LISTAR BODEGAS POR EMPRESA (GET)                                         #
# ------------------------------------------------------------------------- #
class BodegaListAPIView(APIView):
    """
    GET /dm_sistema/logistica/bodegas/
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def get(self, request, *args, **kwargs):
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        qs = Bodega.objects.filter(id_empresa=empresa.id).order_by("nombre_bodega")
        return Response(BodegaSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  OBTENER DETALLE DE BODEGA (POST)                                         #
# ------------------------------------------------------------------------- #
class BodegaDetailAPIView(APIView):
    """
    POST /dm_sistema/logistica/bodegas/detalle/

    Body JSON:
    {
        "id": <int>   # ← id del registro en dm_logistica.bodega
    }

    • Requiere la cookie `auth_token`.
    • Devuelve 404 si la bodega no existe o pertenece a otra empresa.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        # ------------------ 0) Validación de body ----------------------- #
        bod_id = request.data.get("id")
        if bod_id is None:
            return Response({"id": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # ------------------ 1) Verificación de token -------------------- #
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ------------------ 2) Recuperamos la bodega -------------------- #
        try:
            bodega = Bodega.objects.get(pk=bod_id, id_empresa=empresa.id)
        except Bodega.DoesNotExist:
            return Response({"detail": "Bodega no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(BodegaSerializer(bodega).data,
                        status=status.HTTP_200_OK)

# ------------------------------------------------------------------------- #
#  OBTENER DETALLE DE PROVEEDOR (POST)                                      #
# ------------------------------------------------------------------------- #
class ProveedorDetailAPIView(APIView):
    """
    POST /dm_sistema/logistica/proveedores/detalle/
    Body → {"id": <int>}
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        prov_id = request.data.get("id")
        if prov_id is None:
            return Response({"id": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            proveedor = Proveedor.objects.get(pk=prov_id, id_empresa=empresa.id)
        except Proveedor.DoesNotExist:
            return Response({"detail": "Proveedor no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(ProveedorSerializer(proveedor).data,
                        status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  CREAR PROVEEDOR (POST)                                                   #
# ------------------------------------------------------------------------- #
class ProveedorCreateAPIView(APIView):
    """
    POST /dm_sistema/logistica/proveedores/crear/
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        data = _normalize_request_data(request.data)
        data.pop("id_empresa", None)
        data["id_empresa"] = empresa.id
        data.setdefault("fecha_alta", datetime.now().date())

        serializer = ProveedorSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            proveedor = serializer.save()

        return Response(ProveedorSerializer(proveedor).data,
                        status=status.HTTP_201_CREATED)


# ------------------------------------------------------------------------- #
#  CREAR BODEGA (POST)                                                      #
# ------------------------------------------------------------------------- #
class BodegaCreateAPIView(APIView):
    """
    POST /dm_sistema/logistica/bodegas/crear/

    Body JSON:
    {
        "id_bodega_tipo":  <int>,    # obligatorio
        "estado_bodega":   <int>,    # obligatorio
        "nombre_bodega":   "<str>",  # obligatorio
        "nombre_tipo_bodega": "<str>"   # opcional
    }

    El `id_empresa` se asigna automáticamente con la empresa del operador
    autenticado en la cookie.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        # --------------------- token ------------------------------------ #
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # --------------------- datos ------------------------------------ #
        data = _normalize_request_data(request.data)
        data.pop("id_empresa", None)
        data["id_empresa"] = empresa.id

        serializer = BodegaSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            bodega = serializer.save()

        return Response(BodegaSerializer(bodega).data,
                        status=status.HTTP_201_CREATED)


# ------------------------------------------------------------------------- #
#  EDITAR PROVEEDOR (PUT)                                                   #
# ------------------------------------------------------------------------- #
class ProveedorUpdateAPIView(APIView):
    """
    PUT /dm_sistema/logistica/proveedores/editar/
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def put(self, request, *args, **kwargs):
        # ----------------------- 1. Validación de ID ---------------------- #
        prov_id = request.data.get("id")
        if prov_id is None:
            return Response({"id": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # ----------------------- 2. Validación de token ------------------- #
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ----------------------- 3. Obtenemos proveedor ------------------- #
        try:
            proveedor = Proveedor.objects.get(pk=prov_id, id_empresa=empresa.id)
        except Proveedor.DoesNotExist:
            return Response({"detail": "Proveedor no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        # ----------------------- 4. Datos a actualizar -------------------- #
        update_data = _normalize_request_data(request.data)
        update_data.pop("id_empresa", None)
        update_data.pop("id", None)

        # Si `fecha_alta` llega vacía → la removemos para evitar parseo
        if isinstance(update_data.get("fecha_alta"), str) and not update_data["fecha_alta"].strip():
            update_data.pop("fecha_alta")

        serializer = ProveedorSerializer(
            instance=proveedor,
            data=update_data,
            partial=True,       # actualización parcial
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            proveedor = serializer.save()

        return Response(ProveedorSerializer(proveedor).data,
                        status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  EDITAR BODEGA (PUT)                                                      #
# ------------------------------------------------------------------------- #
class BodegaUpdateAPIView(APIView):
    """
    PUT /dm_sistema/logistica/bodegas/editar/

    Body JSON esperado:
    {
        "id":             <int>,          # ← obligatorio
        "id_bodega_tipo": <int>,          # opcional
        "nombre_bodega":  "<str>",        # opcional
        ...
    }

    • Requiere cookie `auth_token`.
    • Solo permite editar bodegas que pertenezcan a la misma empresa del usuario.
    • La actualización es parcial.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def put(self, request, *args, **kwargs):
        # -------------------- 1) Validación de ID ------------------------ #
        bod_id = request.data.get("id")
        if bod_id is None:
            return Response({"id": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # -------------------- 2) Verificación de token ------------------- #
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # -------------------- 3) Recuperamos la bodega ------------------- #
        try:
            bodega = Bodega.objects.get(pk=bod_id, id_empresa=empresa.id)
        except Bodega.DoesNotExist:
            return Response({"detail": "Bodega no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)

        # -------------------- 4) Datos a actualizar ---------------------- #
        update_data = _normalize_request_data(request.data)
        update_data.pop("id_empresa", None)
        update_data.pop("id", None)

        serializer = BodegaSerializer(
            instance=bodega,
            data=update_data,
            partial=True,            # ← permite omitir campos
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            bodega = serializer.save()

        return Response(BodegaSerializer(bodega).data,
                        status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  LISTAR TIPOS DE BODEGA (GET)                                             #
# ------------------------------------------------------------------------- #
class BodegaTipoListAPIView(APIView):
    """
    GET /dm_sistema/logistica/bodegas/tipos/

    • Requiere cookie `auth_token`.
    • Devuelve todos los registros de `dm_logistica.bodega_tipo`.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def get(self, request, *args, **kwargs):
        # ------------------ 1) Verificación de token --------------------- #
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not sesion_activa.id_operador.id_empresa or sesion_activa.id_operador.id_empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ------------------ 2) Listamos tipos de bodega ------------------ #
        qs = BodegaTipo.objects.all().order_by("nombre_tipo_bodega")
        return Response(BodegaTipoSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  OBTENER TIPO DE BODEGA POR ID (POST)                                     #
# ------------------------------------------------------------------------- #
class BodegaTipoDetailAPIView(APIView):
    """
    POST /dm_sistema/logistica/bodegas/tipos/detalle/

    Body JSON:
    {
        "id": <int>   # ← id del registro en dm_logistica.bodega_tipo
    }

    • Requiere la cookie `auth_token`.
    • Devuelve 404 si el tipo de bodega no existe.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        # ------------------ 0) Validación de body ----------------------- #
        tipo_id = request.data.get("id")
        if tipo_id is None:
            return Response({"id": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # ------------------ 1) Verificación de token -------------------- #
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not sesion_activa.id_operador.id_empresa or sesion_activa.id_operador.id_empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ------------------ 2) Recuperamos el tipo ---------------------- #
        try:
            tipo = BodegaTipo.objects.get(pk=tipo_id)
        except BodegaTipo.DoesNotExist:
            return Response({"detail": "Tipo de bodega no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(BodegaTipoSerializer(tipo).data,
                        status=status.HTTP_200_OK)

# ------------------------------------------------------------------------- #
#  LISTAR COMUNAS (GET)                                                     #
# ------------------------------------------------------------------------- #
class ComunaListAPIView(APIView):
    """
    GET /dm_sistema/comunas/

    • Requiere la cookie `auth_token`.
    • Devuelve todas las comunas (`dm_sistema.comuna`) ordenadas por `nombre_comuna`.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def get(self, request, *args, **kwargs):
        # ------------------ 1) Verificación de token -------------------- #
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not sesion_activa.id_operador.id_empresa or sesion_activa.id_operador.id_empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ------------------ 2) Listamos comunas ------------------------- #
        qs = Comuna.objects.all().order_by("nombre_comuna")
        return Response(ComunaSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  LISTAR COMUNAS POR id_region (POST)                                      #
# ------------------------------------------------------------------------- #
class ComunaByRegionAPIView(APIView):
    """
    POST /dm_sistema/comunas/por-region/

    Body JSON:
    {
        "id_region": <int>   # ← id del registro en dm_sistema.region
    }

    • Requiere la cookie `auth_token`.
    • Devuelve todas las comunas cuyo `id_region` coincida con el valor enviado,
      ordenadas por `nombre_comuna`.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        # ------------------ 0) Validación del body ---------------------- #
        id_region = request.data.get("id_region")
        if id_region is None:
            return Response({"id_region": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # ------------------ 1) Verificación de token -------------------- #
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        if (
            not sesion_activa.id_operador.id_empresa
            or sesion_activa.id_operador.id_empresa.estado != 1
        ):
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ------------------ 2) Listamos comunas filtradas --------------- #
        qs = (
            Comuna.objects
            .filter(id_region=id_region)
            .order_by("nombre_comuna")
        )
        return Response(ComunaSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)


# ------------------------------------------------------------------------- #
#  LISTAR REGIONES (GET)                                                    #
# ------------------------------------------------------------------------- #
class RegionListAPIView(APIView):
    """
    GET /dm_sistema/regiones/

    • Requiere la cookie `auth_token`.
    • Devuelve todas las regiones (`dm_sistema.region`) ordenadas por `nombre`.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def get(self, request, *args, **kwargs):
        # ------------------ 1) Verificación de token -------------------- #
        token_cookie = request.COOKIES.get("auth_token")
        if not token_cookie:
            return Response({"detail": "Token no proporcionado"},
                            status=status.HTTP_401_UNAUTHORIZED)

        sesion_activa = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token_cookie)
            .first()
        )
        if not sesion_activa:
            return Response({"detail": "Token inválido o sesión expirada"},
                            status=status.HTTP_401_UNAUTHORIZED)

        if (
            not sesion_activa.id_operador.id_empresa
            or sesion_activa.id_operador.id_empresa.estado != 1
        ):
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ------------------ 2) Listamos regiones ------------------------ #
        qs = Region.objects.all().order_by("nombre")
        return Response(RegionSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)
