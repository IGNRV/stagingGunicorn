# --------------------------------------------------------------------------- #
# ./dm_sistema/views.py                                                       #
# --------------------------------------------------------------------------- #
from __future__ import annotations

import crypt
import secrets
import jwt
import requests
import os
import base64
from datetime import datetime, timezone as dt_timezone
from typing import Any, Dict

from django.conf import settings
from django.db import transaction, connection
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import (
    JSONParser,
    MultiPartParser,
    FormParser,
)

# ------------------------------------------------------------------ #
# MODELOS Y SERIALIZERS                                              #
# ------------------------------------------------------------------ #
from dm_logistica.models import (
    Proveedor,          # crear / listar / obtener / editar proveedor
    Bodega,             # crear / listar / obtener / editar bodegas
    BodegaTipo,         # listar / obtener tipos de bodega
    TipoProducto,       # ← NUEVO: insertar tipo de producto
    MarcaProducto,      # ← NUEVO: insertar marca de producto
    TipoMarcaProducto,  # ← NUEVO: insertar tipo-marca de producto
    ModeloProducto,     # ← NUEVO: insertar modelo de producto
    IdentificadorSerie,
    UnidadMedida,
)
from .models import Operador, Sesiones, SesionesActivas, Comuna, Region
from .serializer import (
    OperadorLoginSerializer,
    OperadorVerificarSerializer,
    OperadorSerializer,
    ProveedorSerializer,
    BodegaSerializer,
    BodegaTipoSerializer,
    BodegaCompletaSerializer,
    TipoProductoSerializer,
    ComunaSerializer,
    RegionSerializer,
    MarcaProductoSerializer,
    TipoMarcaProductoSerializer,
    ModeloProductoCompletoSerializer,
    ModeloProductoCompletoDetalleSerializer,
    IdentificadorSerieSerializer,
    UnidadMedidaSerializer,
    TipoMarcaProductoJoinSerializer,
)
from dm_logistica.serializer import ModeloProductoSerializer  # ← import del serializer

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
#  CREAR TIPO DE PRODUCTO (POST)                                            #
# ------------------------------------------------------------------------- #
class TipoProductoCreateAPIView(APIView):
    """
    POST /dm_sistema/logistica/tipos-producto/crear/

    Body JSON:
    {
        "codigo_tipo_producto": "<str>",
        "nombre_tipo_producto": "<str>",
        "estado":               <int>,
        "correlativo_desde":    <int>,   # opcional
        "correlativo_hasta":    <int>    # opcional
    }

    • `id_empresa` se asigna automáticamente con la empresa asociada al operador
      autenticado (cookie `auth_token`).
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
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

        # ------------------ 2) Normalizamos data ------------------------ #
        data = _normalize_request_data(request.data)
        data.pop("id_empresa", None)
        data["id_empresa"] = empresa.id

        serializer = TipoProductoSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # ------------------ 3) Guardamos registro ----------------------- #
        with transaction.atomic():
            tipo_prod = serializer.save()

        return Response(TipoProductoSerializer(tipo_prod).data,
                        status=status.HTTP_201_CREATED)
# ------------------------------------------------------------------------- #
#  LISTAR TIPOS DE PRODUCTO POR EMPRESA (GET)                                #
# ------------------------------------------------------------------------- #
class TipoProductoListAPIView(APIView):
    """
    GET /dm_sistema/logistica/tipos-producto/

    • Requiere la cookie `auth_token`.
    • Devuelve todos los registros de `dm_logistica.tipo_producto` cuyo
      `id_empresa` coincide con el de la empresa asociada al operador.
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

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ------------------ 2) Listamos tipos de producto --------------- #
        qs = (
            TipoProducto.objects
            .filter(id_empresa=empresa.id)
            .order_by("nombre_tipo_producto")
        )
        return Response(TipoProductoSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)
# ------------------------------------------------------------------------- #
#  EDITAR TIPO DE PRODUCTO (PUT)                                            #
# ------------------------------------------------------------------------- #
class TipoProductoUpdateAPIView(APIView):
    """
    PUT /dm_sistema/logistica/tipos-producto/editar/

    Body JSON esperado:
    {
        "id":                 <int>,          # ← obligatorio
        "codigo_tipo_producto": "<str>",      # opcional
        "nombre_tipo_producto": "<str>",      # opcional
        "estado":               <int>,        # opcional
        "correlativo_desde":    <int>,        # opcional
        "correlativo_hasta":    <int>         # opcional
    }

    • Requiere cookie `auth_token`.
    • Solo permite editar registros que pertenezcan a la misma empresa
      del operador autenticado.
    • La actualización es parcial.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def put(self, request, *args, **kwargs):
        # ------------------ 0) Validación de ID ------------------------ #
        tipo_id = request.data.get("id")
        if tipo_id is None:
            return Response({"id": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # ------------------ 1) Verificación de token ------------------- #
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

        # ------------------ 2) Recuperamos tipo de producto ------------ #
        try:
            tipo_prod = TipoProducto.objects.get(pk=tipo_id, id_empresa=empresa.id)
        except TipoProducto.DoesNotExist:
            return Response({"detail": "Tipo de producto no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        # ------------------ 3) Datos a actualizar ---------------------- #
        update_data = _normalize_request_data(request.data)
        update_data.pop("id_empresa", None)
        update_data.pop("id", None)

        serializer = TipoProductoSerializer(
            instance=tipo_prod,
            data=update_data,
            partial=True,           # ← permite omitir campos
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # ------------------ 4) Guardamos cambios ----------------------- #
        with transaction.atomic():
            tipo_prod = serializer.save()

        return Response(TipoProductoSerializer(tipo_prod).data,
                        status=status.HTTP_200_OK)

# ------------------------------------------------------------------------- #
#  DETALLE  TIPO DE PRODUCTO (POST)                                         #
# ------------------------------------------------------------------------- #
class TipoProductoDetailAPIView(APIView):
    """
    POST /dm_sistema/logistica/tipos-producto/detalle/

    Body JSON:
    {
        "id": <int>   # ← id del registro en dm_logistica.tipo_producto
    }

    • Requiere la cookie `auth_token`.
    • Devuelve 404 si el tipo de producto no existe o pertenece a otra empresa.
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

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response({"detail": "La empresa asociada se encuentra inactiva."},
                            status=status.HTTP_403_FORBIDDEN)

        # ------------------ 2) Recuperamos el tipo de producto ---------- #
        try:
            tipo_prod = TipoProducto.objects.get(pk=tipo_id, id_empresa=empresa.id)
        except TipoProducto.DoesNotExist:
            return Response({"detail": "Tipo de producto no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(TipoProductoSerializer(tipo_prod).data,
                        status=status.HTTP_200_OK)
    
# ------------------------------------------------------------------------- #
#  LISTAR MARCAS DE PRODUCTO POR EMPRESA (GET)                              #
# ------------------------------------------------------------------------- #
class MarcaProductoListAPIView(APIView):
    """
    GET /dm_sistema/logistica/marcas-producto/

    • Requiere la cookie `auth_token`.
    • Devuelve todas las marcas de producto (`dm_logistica.marca_producto`)
      cuyo `id_empresa` coincide con el de la empresa asociada al operador.
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

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ------------------ 2) Listamos marcas de producto -------------- #
        qs = (
            MarcaProducto.objects
            .filter(id_empresa=empresa.id)
            .order_by("nombre_marca_producto")
        )
        return Response(MarcaProductoSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)

# ------------------------------------------------------------------------- #
#  CREAR MARCA DE PRODUCTO (POST)                                           #
# ------------------------------------------------------------------------- #
class MarcaProductoCreateAPIView(APIView):
    """
    POST /dm_sistema/logistica/marcas-producto/crear/

    Body JSON:
    {
        "nombre_marca_producto": "<str>",
        "estado":                <int>
    }

    • `id_empresa` se asigna automáticamente con la empresa asociada al
      operador autenticado (cookie `auth_token`).
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
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
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ------------------ 2) Normalizamos data ------------------------ #
        data = _normalize_request_data(request.data)
        data.pop("id_empresa", None)
        data["id_empresa"] = empresa.id

        serializer = MarcaProductoSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # ------------------ 3) Guardamos registro ----------------------- #
        with transaction.atomic():
            marca = serializer.save()

        return Response(MarcaProductoSerializer(marca).data,
                        status=status.HTTP_201_CREATED)
    
# ------------------------------------------------------------------------- #
#  EDITAR MARCA DE PRODUCTO (PUT)                                           #
# ------------------------------------------------------------------------- #
class MarcaProductoUpdateAPIView(APIView):
    """
    PUT /dm_sistema/logistica/marcas-producto/editar/

    Body JSON esperado:
    {
        "id":                  <int>,   # obligatorio
        "nombre_marca_producto": "<str>",  # opcional
        "estado":                <int>     # opcional
    }

    • Requiere cookie `auth_token`.
    • Solo permite editar registros que pertenezcan a la misma empresa
      del operador autenticado.
    • La actualización es parcial.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def put(self, request, *args, **kwargs):
        # ------------------ 0) Validación de ID ------------------------ #
        marca_id = request.data.get("id")
        if marca_id is None:
            return Response({"id": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # ------------------ 1) Verificación de token ------------------- #
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

        # ------------------ 2) Recuperamos marca de producto ----------- #
        try:
            marca = MarcaProducto.objects.get(pk=marca_id, id_empresa=empresa.id)
        except MarcaProducto.DoesNotExist:
            return Response({"detail": "Marca de producto no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)

        # ------------------ 3) Datos a actualizar ---------------------- #
        update_data = _normalize_request_data(request.data)
        update_data.pop("id_empresa", None)
        update_data.pop("id", None)

        serializer = MarcaProductoSerializer(
            instance=marca,
            data=update_data,
            partial=True,          # permite omitir campos
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # ------------------ 4) Guardamos cambios ----------------------- #
        with transaction.atomic():
            marca = serializer.save()

        return Response(MarcaProductoSerializer(marca).data,
                        status=status.HTTP_200_OK)

# ------------------------------------------------------------------------- #
#  DETALLE MARCA DE PRODUCTO (POST)                                         #
# ------------------------------------------------------------------------- #
class MarcaProductoDetailAPIView(APIView):
    """
    POST /dm_sistema/logistica/marcas-producto/detalle/

    Body JSON:
    {
        "id": <int>   # ← id del registro en dm_logistica.marca_producto
    }

    • Requiere la cookie `auth_token`.
    • Devuelve 404 si la marca de producto no existe o pertenece a otra empresa.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        # ------------------ 0) Validación de body ----------------------- #
        marca_id = request.data.get("id")
        if marca_id is None:
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

        # ------------------ 2) Recuperamos la marca --------------------- #
        try:
            marca = MarcaProducto.objects.get(pk=marca_id, id_empresa=empresa.id)
        except MarcaProducto.DoesNotExist:
            return Response({"detail": "Marca de producto no encontrada"},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(MarcaProductoSerializer(marca).data,
                        status=status.HTTP_200_OK)

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
# ------------------------------------------------------------------------- #
#  CREAR TIPO-MARCA PRODUCTO (POST)                                         #
# ------------------------------------------------------------------------- #
class TipoMarcaProductoCreateAPIView(APIView):
    """
    POST /dm_sistema/logistica/tipo-marca-producto/crear/

    Body JSON:
    {
        "id_tipo_producto":  <int>,
        "id_marca_producto": <int>
    }

    • `id_empresa` se asigna automáticamente con la empresa asociada al
      operador autenticado (cookie `auth_token`).
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        # 1) Verificación de token
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
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2) Normalizamos y armamos data
        data = _normalize_request_data(request.data)
        data.pop("id_empresa", None)
        data["id_empresa"] = empresa.id

        serializer = TipoMarcaProductoSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 3) Guardamos registro
        with transaction.atomic():
            tipo_marca = serializer.save()

        return Response(TipoMarcaProductoSerializer(tipo_marca).data,
                        status=status.HTTP_201_CREATED)
# ------------------------------------------------------------------------- #
#  LISTAR TIPO-MARCA PRODUCTO (GET)                                         #
# ------------------------------------------------------------------------- #
class TipoMarcaProductoListAPIView(APIView):
    """
    GET /dm_sistema/logistica/tipo-marca-producto/

    • Requiere la cookie `auth_token`.
    • Devuelve todos los registros de `dm_logistica.tipo_marca_producto`
      cuyo `id_empresa` coincide con la empresa asociada al operador.
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
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        qs = (
            TipoMarcaProducto.objects
            .filter(id_empresa=empresa.id)
            .order_by("id_tipo_producto", "id_marca_producto")
        )
        return Response(TipoMarcaProductoSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)
# ------------------------------------------------------------------------- #
#  EDITAR TIPO-MARCA PRODUCTO (PUT)                                         #
# ------------------------------------------------------------------------- #
class TipoMarcaProductoUpdateAPIView(APIView):
    """
    PUT /dm_sistema/logistica/tipo-marca-producto/editar/

    Body JSON esperado:
    {
        "id":                <int>,  # ← id de dm_logistica.tipo_marca_producto
        "id_tipo_producto":  <int>,  # opcional
        "id_marca_producto": <int>,  # opcional
    }

    • Requiere la cookie `auth_token`.
    • Solo permite editar la fila cuyo id y id_empresa coinciden con el
      operador autenticado.
    • Actualización parcial.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def put(self, request, *args, **kwargs):
        # 0) Validación de ID
        registro_id = request.data.get("id")
        if registro_id is None:
            return Response({"id": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # 1) Verificación de token
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

        # 2) Recuperamos registro
        try:
            registro = TipoMarcaProducto.objects.get(pk=registro_id, id_empresa=empresa.id)
        except TipoMarcaProducto.DoesNotExist:
            return Response({"detail": "Registro no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        # 3) Normalizamos data y preparamos actualización
        update_data = _normalize_request_data(request.data)
        update_data.pop("id", None)
        update_data.pop("id_empresa", None)

        serializer = TipoMarcaProductoSerializer(
            instance=registro,
            data=update_data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 4) Guardamos cambios
        with transaction.atomic():
            registro_actualizado = serializer.save()

        return Response(TipoMarcaProductoSerializer(registro_actualizado).data,
                        status=status.HTTP_200_OK)
# ------------------------------------------------------------------------- #
#  DETALLE TIPO-MARCA PRODUCTO (POST)                                       #
# ------------------------------------------------------------------------- #
class TipoMarcaProductoDetailAPIView(APIView):
    """
    POST /dm_sistema/logistica/tipo-marca-producto/detalle/

    Body JSON:
    {
        "id": <int>  # id de dm_logistica.tipo_marca_producto
    }

    • Requiere cookie `auth_token`.
    • Devuelve 404 si no existe o pertenece a otra empresa.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        tipo_marca_id = request.data.get("id")
        if tipo_marca_id is None:
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
            tipo_marca = TipoMarcaProducto.objects.get(pk=tipo_marca_id, id_empresa=empresa.id)
        except TipoMarcaProducto.DoesNotExist:
            return Response({"detail": "Tipo-Marca de producto no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(TipoMarcaProductoSerializer(tipo_marca).data,
                        status=status.HTTP_200_OK)
# ------------------------------------------------------------------------- #
#  ELIMINAR TIPO-MARCA PRODUCTO (DELETE)                                    #
# ------------------------------------------------------------------------- #
class TipoMarcaProductoDeleteAPIView(APIView):
    """
    DELETE /dm_sistema/logistica/tipo-marca-producto/eliminar/

    Body JSON:
    {
        "id": <int>
    }

    • Requiere la cookie `auth_token`.
    • Elimina el registro cuyo `id` e `id_empresa` coinciden con el operador autenticado.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def delete(self, request, *args, **kwargs):
        # 0) Validación de ID
        registro_id = request.data.get("id")
        if registro_id is None:
            return Response({"id": ["Este campo es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # 1) Verificación de token
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

        # 2) Recuperamos y eliminamos el registro
        try:
            registro = TipoMarcaProducto.objects.get(pk=registro_id, id_empresa=empresa.id)
        except TipoMarcaProducto.DoesNotExist:
            return Response({"detail": "Registro no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            registro.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

# ------------------------------------------------------------------------- #
#  CREAR MODELO PRODUCTO (POST)                                             #
# ------------------------------------------------------------------------- #
class ModeloProductoCreateAPIView(APIView):
    """
    POST /dm_sistema/logistica/modelo-producto/crear/

    A partir de ahora se acepta el archivo de imagen mediante multipart/form-data:
        - la clave debe ser **imagen_file** (no "imagen").
        - todos los demás campos pueden ir como texto dentro del mismo FormData.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    # --- NUEVO: habilitamos los parsers para multipart/form-data -------- #
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        # ------------------ 1. Verificación de cookie/token -------------- #
        token = request.COOKIES.get("auth_token")
        if not token:
            return Response(
                {"detail": "Token no proporcionado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        sesion = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token)
            .first()
        )
        if not sesion:
            return Response(
                {"detail": "Token inválido o sesión expirada"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        empresa = sesion.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ------------------ 2. Preparamos el payload --------------------- #
        #   • Usamos `request.data` DIRECTAMENTE para no perder el file.
        data = request.data.copy()

        # Si el cliente no envía id_empresa, usamos el de la sesión
        data.setdefault("id_empresa", empresa.id)

        # ------------------ 3. Serializamos & validamos ------------------ #
        serializer = ModeloProductoSerializer(
            data=data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------ 4. Guardamos transaccionalmente -------------- #
        with transaction.atomic():
            modelo = serializer.save()

        return Response(
            ModeloProductoSerializer(modelo).data,
            status=status.HTTP_201_CREATED,
        )
# ------------------------------------------------------------------------- #
#  EDITAR MODELO DE PRODUCTO (PUT) – ACEPTA IMAGEN IGUAL QUE “CREATE”       #
# ------------------------------------------------------------------------- #
class ModeloProductoUpdateAPIView(APIView):
    """
    PUT /dm_sistema/logistica/modelo-producto/editar/

    A partir de ahora admite multipart/form-data para que el frontend pueda
    enviar un archivo de imagen con la clave **imagen_file** (tal como en
    ModeloProductoCreateAPIView).

    Campos mínimos en el FormData:
        • id_modelo_producto        (int)   ← obligatorio
        • imagen_file               (file)  ← opcional
        • ...cualquier otro campo del modelo que se desee actualizar.

    El resto de la lógica (autorización por empresa, validaciones, etc.)
    permanece intacta.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    # --- NUEVO: habilitamos parsers para multipart/form-data ------------- #
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def put(self, request, *args, **kwargs):
        # ------------------ 0) Validación de ID ------------------------- #
        modelo_id = request.data.get("id_modelo_producto")
        if modelo_id is None:
            return Response(
                {"id_modelo_producto": ["Este campo es obligatorio."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------ 1) Verificación de token -------------------- #
        token = request.COOKIES.get("auth_token")
        if not token:
            return Response(
                {"detail": "Token no proporcionado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        sesion = (
            SesionesActivas.objects
            .select_related("id_operador", "id_operador__id_empresa")
            .filter(token=token)
            .first()
        )
        if not sesion:
            return Response(
                {"detail": "Token inválido o sesión expirada"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        empresa = sesion.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ------------------ 2) Recuperamos el modelo -------------------- #
        try:
            modelo = ModeloProducto.objects.get(
                pk=modelo_id,
                id_empresa=empresa.id,
            )
        except ModeloProducto.DoesNotExist:
            return Response(
                {"detail": "Modelo de producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ------------------ 3) Preparamos los datos --------------------- #
        # Usamos `request.data` directamente para conservar el archivo.
        data = request.data.copy()          # ➜ MultiValueDict seguro

        # • Garantizamos que el registro no cambie de empresa
        data.setdefault("id_empresa", empresa.id)

        # • Nunca permitimos cambiar la PK
        data.pop("id_modelo_producto", None)

        # ------------------ 4) Serializamos & validamos ----------------- #
        serializer = ModeloProductoSerializer(
            instance=modelo,
            data=data,               # incluye imagen_file si viene
            partial=True,            # actualización parcial
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------ 5) Guardamos cambios ------------------------ #
        with transaction.atomic():
            modelo_actualizado = serializer.save()  # `imagen_file` ya gestionado

        return Response(
            ModeloProductoSerializer(modelo_actualizado).data,
            status=status.HTTP_200_OK,
        )
# ------------------------------------------------------------------------- #
#  LISTAR MODELOS DE PRODUCTO POR EMPRESA (GET)                             #
# ------------------------------------------------------------------------- #
class ModeloProductoListAPIView(APIView):
    """
    GET /dm_sistema/logistica/modelo-producto/

    • Requiere la cookie `auth_token`.
    • Devuelve todos los registros de `dm_logistica.modelo_producto`
      cuyo `id_empresa` coincide con la empresa del operador autenticado.
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

        qs = ModeloProducto.objects.filter(id_empresa=empresa.id).order_by("nombre_modelo")
        return Response(ModeloProductoSerializer(qs, many=True).data,
                        status=status.HTTP_200_OK)
# ------------------------------------------------------------------------- #
#  NUEVO ENDPOINT → LISTAR BODEGAS “COMPLETAS”                             #
# ------------------------------------------------------------------------- #
class BodegaCompletaListAPIView(APIView):
    """
    GET /dm_sistema/logistica/bodegas-completas/

    • Requiere la cookie `auth_token`.
    • Devuelve todos los registros con JOIN entre bodega y bodega_tipo
      filtrados por id_empresa del operador autenticado.
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

        # Ejecutamos el JOIN filtrado por la empresa
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                  b.id,
                  b.id_empresa,
                  bt.nombre_tipo_bodega,
                  b.estado_bodega,
                  b.nombre_bodega
                FROM dm_logistica.bodega b
                INNER JOIN dm_logistica.bodega_tipo bt
                  ON b.id_bodega_tipo = bt.id
                WHERE b.id_empresa = %s
                ORDER BY b.nombre_bodega
            """, [empresa.id])
            rows = cursor.fetchall()

        data = [
            {
                "id": row[0],
                "id_empresa": row[1],
                "nombre_tipo_bodega": row[2],
                "estado_bodega": row[3],
                "nombre_bodega": row[4],
            }
            for row in rows
        ]

        return Response(BodegaCompletaSerializer(data, many=True).data,
                        status=status.HTTP_200_OK)
# ------------------------------------------------------------------------- #
#  NUEVO ENDPOINT → DETALLE MODELO DE PRODUCTO (POST)                       #
# ------------------------------------------------------------------------- #
class ModeloProductoDetailAPIView(APIView):
    """
    POST /dm_sistema/logistica/modelo-producto/detalle/

    Body JSON:
    {
        "id_modelo_producto": <int>
    }

    • Requiere la cookie `auth_token`.
    • Devuelve 404 si el modelo no existe o pertenece a otra empresa.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        # 0) Validación de body
        modelo_id = request.data.get("id_modelo_producto")
        if modelo_id is None:
            return Response(
                {"id_modelo_producto": ["Este campo es obligatorio."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1) Verificación de token
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
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2) Recuperamos el modelo
        try:
            modelo = ModeloProducto.objects.get(
                pk=modelo_id,
                id_empresa=empresa.id
            )
        except ModeloProducto.DoesNotExist:
            return Response({"detail": "Modelo de producto no encontrado"},
                            status=status.HTTP_404_NOT_FOUND)

        # 3) Devolvemos el registro
        return Response(
            ModeloProductoSerializer(modelo).data,
            status=status.HTTP_200_OK
        )
# ------------------------------------------------------------------------- #
#  NUEVO ENDPOINT → LISTAR MODELOS DE PRODUCTO “COMPLETOS” (GET)             #
# ------------------------------------------------------------------------- #
class ModeloProductoCompletoListAPIView(APIView):
    """
    GET /dm_sistema/logistica/modelos-producto-completos/

    • Requiere la cookie `auth_token`.
    • Devuelve todos los registros de modelo_producto
      junto con tipo, marca y unidad de medida,
      filtrados por la empresa del operador autenticado.
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

        # Ejecutamos la consulta con JOINs y filtrado por id_empresa
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    mp.id_modelo_producto,
                    mp.id_empresa,
                    tp.codigo_tipo_producto,
                    tp.nombre_tipo_producto,
                    mpd.nombre_marca_producto,
                    um.nombre_unidad_medida,
                    mp.id_identificador_serie,
                    mp.codigo_interno,
                    mp.fccid,
                    mp.sku,
                    mp.sku_codigo,
                    mp.nombre_modelo,
                    mp.descripcion,
                    mp.imagen,
                    mp.estado,
                    mp.producto_seriado,
                    mp.nombre_comercial,
                    mp.despacho_express,
                    mp.rebaja_consumo,
                    mp.dias_rebaja_consumo,
                    mp.orden_solicitud_despacho
                FROM dm_logistica.modelo_producto AS mp
                JOIN dm_logistica.tipo_marca_producto AS tmp
                  ON mp.id_tipo_marca_producto = tmp.id
                JOIN dm_logistica.tipo_producto AS tp
                  ON tmp.id_tipo_producto = tp.id
                JOIN dm_logistica.marca_producto AS mpd
                  ON tmp.id_marca_producto = mpd.id
                JOIN dm_logistica.unidad_medida AS um
                  ON mp.id_unidad_medida = um.id
                WHERE mp.id_empresa = %s
                ORDER BY mp.nombre_modelo
            """, [empresa.id])
            rows = cursor.fetchall()

        data = [
            {
                "id_modelo_producto":       row[0],
                "id_empresa":               row[1],
                "codigo_tipo_producto":     row[2],
                "nombre_tipo_producto":     row[3],
                "nombre_marca_producto":    row[4],
                "nombre_unidad_medida":     row[5],
                "id_identificador_serie":   row[6],
                "codigo_interno":           row[7],
                "fccid":                    row[8],
                "sku":                      row[9],
                "sku_codigo":               row[10],
                "nombre_modelo":            row[11],
                "descripcion":              row[12],
                "imagen":                   row[13],
                "estado":                   row[14],
                "producto_seriado":         row[15],
                "nombre_comercial":         row[16],
                "despacho_express":         row[17],
                "rebaja_consumo":           row[18],
                "dias_rebaja_consumo":      row[19],
                "orden_solicitud_despacho": row[20],
            }
            for row in rows
        ]

        serializer = ModeloProductoCompletoSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
# ------------------------------------------------------------------------- #
#  NUEVO ENDPOINT → LISTAR IDENTIFICADORES DE SERIE (GET)                   #
# ------------------------------------------------------------------------- #
class IdentificadorSerieListAPIView(APIView):
    """
    GET /dm_sistema/logistica/identificadores-serie/

    • Requiere la cookie `auth_token`.
    • Devuelve todos los registros de `dm_logistica.identificador_serie`.
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
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        qs = IdentificadorSerie.objects.all().order_by("nombre_serie")
        return Response(
            IdentificadorSerieSerializer(qs, many=True).data,
            status=status.HTTP_200_OK
        )
# ------------------------------------------------------------------------- #
#  NUEVO ENDPOINT → LISTAR UNIDADES DE MEDIDA (GET)                         #
# ------------------------------------------------------------------------- #
class UnidadMedidaListAPIView(APIView):
    """
    GET /dm_sistema/logistica/unidades-medida/

    • Requiere la cookie `auth_token`.
    • Devuelve todos los registros de `dm_logistica.unidad_medida`.
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
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        qs = UnidadMedida.objects.all().order_by("nombre_unidad_medida")
        return Response(
            UnidadMedidaSerializer(qs, many=True).data,
            status=status.HTTP_200_OK
        )
# ------------------------------------------------------------------------- #
#  NUEVO ENDPOINT → DETALLE MODELO “COMPLETO” CON IMAGEN                    #
# ------------------------------------------------------------------------- #
class ModeloProductoCompletoDetailAPIView(APIView):
    """
    POST /dm_sistema/logistica/modelo-producto-completo/

    Body JSON:
    {
        "id_modelo_producto": <int>
    }

    • Requiere la cookie `auth_token`.
    • Devuelve el registro solicitado (JOINs) **más** la imagen codificada
      en base64; si el archivo no existe se retorna `null` en `imagen_base64`.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        # ---------------- 0) Validación de body ------------------------ #
        modelo_id = request.data.get("id_modelo_producto")
        if modelo_id is None:
            return Response(
                {"id_modelo_producto": ["Este campo es obligatorio."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------- 1) Verificación de token --------------------- #
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

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ---------------- 2) Ejecutamos la query ----------------------- #
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    mp.id_modelo_producto,
                    mp.id_empresa,
                    tp.codigo_tipo_producto,
                    tp.nombre_tipo_producto,
                    mpd.nombre_marca_producto,
                    um.nombre_unidad_medida,
                    mp.id_identificador_serie,
                    mp.codigo_interno,
                    mp.fccid,
                    mp.sku,
                    mp.sku_codigo,
                    mp.nombre_modelo,
                    mp.descripcion,
                    mp.imagen,
                    mp.estado,
                    mp.producto_seriado,
                    mp.nombre_comercial,
                    mp.despacho_express,
                    mp.rebaja_consumo,
                    mp.dias_rebaja_consumo,
                    mp.orden_solicitud_despacho
                FROM dm_logistica.modelo_producto AS mp
                JOIN dm_logistica.tipo_marca_producto AS tmp
                  ON mp.id_tipo_marca_producto = tmp.id
                JOIN dm_logistica.tipo_producto AS tp
                  ON tmp.id_tipo_producto = tp.id
                JOIN dm_logistica.marca_producto AS mpd
                  ON tmp.id_marca_producto = mpd.id
                JOIN dm_logistica.unidad_medida AS um
                  ON mp.id_unidad_medida = um.id
                WHERE mp.id_empresa = %s
                  AND mp.id_modelo_producto = %s
                """, [empresa.id, modelo_id])
            row = cursor.fetchone()

        if not row:
            return Response(
                {"detail": "Modelo de producto no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            "id_modelo_producto":       row[0],
            "id_empresa":               row[1],
            "codigo_tipo_producto":     row[2],
            "nombre_tipo_producto":     row[3],
            "nombre_marca_producto":    row[4],
            "nombre_unidad_medida":     row[5],
            "id_identificador_serie":   row[6],
            "codigo_interno":           row[7],
            "fccid":                    row[8],
            "sku":                      row[9],
            "sku_codigo":               row[10],
            "nombre_modelo":            row[11],
            "descripcion":              row[12],
            "imagen":                   row[13],
            "estado":                   row[14],
            "producto_seriado":         row[15],
            "nombre_comercial":         row[16],
            "despacho_express":         row[17],
            "rebaja_consumo":           row[18],
            "dias_rebaja_consumo":      row[19],
            "orden_solicitud_despacho": row[20],
        }

        # ---------------- 3) Leemos la imagen -------------------------- #
        img_b64: str | None = None
        if data["imagen"]:
            # Ruta absoluta: BASE_DIR + imagen sin slash inicial
            abs_path = os.path.join(
                str(settings.BASE_DIR),
                data["imagen"].lstrip("/"),
            )
            try:
                with open(abs_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode("utf-8")
            except FileNotFoundError:
                img_b64 = None

        data["imagen_base64"] = img_b64

        # Serializamos la respuesta
        serializer = ModeloProductoCompletoDetalleSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
# ------------------------------------------------------------------------- #
#  ★ NUEVO ENDPOINT – DETALLE JOIN TIPO‑MARCA‑PRODUCTO (POST)               #
# ------------------------------------------------------------------------- #
class TipoMarcaProductoJoinDetailAPIView(APIView):
    """
    POST /dm_sistema/logistica/tipo-marca-producto-completo/

    Body JSON:
    {
        "id_tipo_marca_producto": <int>
    }

    • Requiere la cookie `auth_token`.
    • Devuelve la fila de la relación tipo‑marca con los datos descriptivos
      del tipo y la marca filtrados por la empresa del operador autenticado.
    """
    authentication_classes: list = []
    permission_classes:     list = []

    def post(self, request, *args, **kwargs):
        # ---------------- 0) Validación de body ------------------------- #
        registro_id = request.data.get("id_tipo_marca_producto")
        if registro_id is None:
            return Response(
                {"id_tipo_marca_producto": ["Este campo es obligatorio."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------- 1) Verificación de token ---------------------- #
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

        empresa = sesion_activa.id_operador.id_empresa
        if not empresa or empresa.estado != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ---------------- 2) Ejecutamos la query ------------------------ #
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    tmp.id,
                    tmp.id_empresa,
                    tp.codigo_tipo_producto,
                    tp.nombre_tipo_producto,
                    mp.nombre_marca_producto
                FROM dm_logistica.tipo_marca_producto  AS tmp
                JOIN dm_logistica.tipo_producto        AS tp
                  ON tp.id = tmp.id_tipo_producto
                JOIN dm_logistica.marca_producto       AS mp
                  ON mp.id = tmp.id_marca_producto
                WHERE tmp.id_empresa = %s
                  AND tmp.id = %s
                """,
                [empresa.id, registro_id],
            )
            row = cursor.fetchone()

        if not row:
            return Response(
                {"detail": "Registro no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            "id_tipo_marca_producto": row[0],
            "id_empresa":             row[1],
            "codigo_tipo_producto":   row[2],
            "nombre_tipo_producto":   row[3],
            "nombre_marca_producto":  row[4],
        }

        serializer = TipoMarcaProductoJoinSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)