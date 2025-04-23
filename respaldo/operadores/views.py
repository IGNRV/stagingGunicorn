# ./operadores/views.py

from __future__ import annotations

import os
import jwt
import secrets
import requests
import crypt                              # misma sal BlowFish heredada
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Operador, OperadorBodega, OperadorEmpresaModulo,
    OperadorEmpresaModuloMenu, OperadorGrupo, OperadorPuntoVenta,
    Sesion, SesionActiva
)
from .serializer import (
    OperadorSerializer, OperadorBodegaSerializer,
    OperadorEmpresaModuloSerializer, OperadorEmpresaModuloMenuSerializer,
    OperadorGrupoSerializer, OperadorPuntoVentaSerializer,
    SesionSerializer, SesionActivaSerializer,
    ProveedorSerializer            # ← añadimos import
)
from dm_logistica.models import Proveedor  # ← añadimos import


# ---------------------------------------------------------------------
#  CORS mínimo ─ permite varios orígenes (prod + dev) -----------------
# ---------------------------------------------------------------------
class RestrictToReactMixin:
    """
    Permite la petición solo si la cabecera **Origin** está incluida en
    la lista blanca.  
    · Si el navegador NO envía cabecera Origin (p.e. cURL / Postman)
      la solicitud se acepta.  
    · La lista se puede ampliar vía variable de entorno
      «ALLOWED_CORS_ORIGINS», separada por comas.
    """
    _BASE_ORIGINS = {
        "http://localhost:5173",          # desarrollo local
        "https://desarrollo.smartgest.cl" # build de desarrollo
    }

    # leemos orígenes extra definidos en variables de entorno
    EXTRA_ORIGINS = set(
        origin.strip()
        for origin in os.getenv("ALLOWED_CORS_ORIGINS", "").split(",")
        if origin.strip()
    )

    ALLOWED_ORIGINS = _BASE_ORIGINS | EXTRA_ORIGINS

    def initial(self, request, *args, **kwargs):
        origin = request.META.get("HTTP_ORIGIN")

        # «None» → llamada sin cabecera Origin (Postman, misma página, etc.)
        if origin is not None and origin not in self.ALLOWED_ORIGINS:
            raise PermissionDenied("Acceso denegado por CORS.")

        return super().initial(request, *args, **kwargs)


# ---------------------------------------------------------------------
#  utilidades auxiliares
# ---------------------------------------------------------------------
def enviar_correo_python(
    remitente: str, correo_destino: str, asunto: str, detalle: str
) -> None:
    """Consume el micro‑servicio PHP legado que envía correos."""
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


# ---------------------------------------------------------------------
#  VIEWSET PRINCIPAL  (login / 2FA / logout)
# ---------------------------------------------------------------------
class OperadorViewSet(RestrictToReactMixin, viewsets.ModelViewSet):
    queryset = Operador.objects.all()
    serializer_class = OperadorSerializer

    # ============================================================== #
    # 1) LOGIN ------------------------------------------------------ #
    # ============================================================== #
    @action(detail=False, methods=["post"])
    def validar(self, request):
        """
        POST /operadores/operadores/validar/
        """
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Se requieren 'username' y 'password'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ───────── validación de credenciales ─────────
        try:
            op = Operador.objects.get(username=username)
        except Operador.DoesNotExist:
            return Response(
                {"error": "No existe un operador con esos datos."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if op.estado != 1:
            return Response(
                {"error": "El usuario no se encuentra activo."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if op.id_empresa.estado != 1:
            return Response(
                {"error": "La empresa asociada al usuario no se encuentra activa."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if op.conexion_fallida > 2:
            return Response(
                {"error": "Ha superado los intentos permitidos (3). Cuenta bloqueada."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # contraseña (hash BlowFish heredado)
        if crypt.crypt(password, op.password) != op.password:
            op.conexion_fallida += 1
            op.save(update_fields=["conexion_fallida"])
            return Response(
                {"error": "Credenciales incorrectas."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # reset de fallos
        if op.conexion_fallida:
            op.conexion_fallida = 0
            op.save(update_fields=["conexion_fallida"])

        # JWT por 24 h
        token = jwt.encode(
            {
                "id":       op.id,
                "username": op.username,
                "exp":      datetime.utcnow() + timedelta(hours=24),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        # IP real
        ip = request.META.get("HTTP_X_FORWARDED_FOR",
                              request.META.get("REMOTE_ADDR", ""))
        if "," in ip:
            ip = ip.split(",")[0].strip()

        # sesión + 2FA
        sesion = Sesion.objects.create(
            ip=ip,
            fecha=timezone.now(),
            id_operador=op,
            id_empresa=op.id_empresa,
        )
        codigo = secrets.token_hex(16)
        SesionActiva.objects.create(
            id_operador=op,
            id_sesion=sesion,
            id_empresa=op.id_empresa,
            fecha_registro=timezone.now(),
            token=token,
            cod_verificacion=codigo,
        )

        enviar_correo_python(
            "DM", op.username, "Código de Verificación",
            f"Hola, tu código es: {codigo}"
        )

        return Response({"username": op.username}, status=status.HTTP_200_OK)

    # ============================================================== #
    # 2) 2FA / VERIFICAR ------------------------------------------- #
    # ============================================================== #
    @action(detail=False, methods=["post"])
    def verificar(self, request):
        """
        POST /operadores/operadores/verificar/
        """
        username = request.data.get("username")
        codigo   = request.data.get("cod_verificacion")

        if not username or not codigo:
            return Response(
                {"error": "Se requieren 'username' y 'cod_verificacion'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sesiones = (
            SesionActiva.objects
            .filter(id_operador__username=username)
            .order_by("-fecha_registro")
        )
        if not sesiones.exists():
            return Response(
                {"error": "No se encontró ninguna sesión activa para este operador."},
                status=status.HTTP_404_NOT_FOUND,
            )

        sesion_reciente = sesiones.first()
        if sesion_reciente.cod_verificacion != codigo:
            return Response(
                {"error": "El código de verificación no coincide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        op = sesion_reciente.id_operador

        # dejamos solo la sesión validada
        SesionActiva.objects.filter(id_operador=op).exclude(
            id=sesion_reciente.id).delete()

        if op.id_empresa.estado != 1:
            sesion_reciente.delete()
            return Response(
                {"error": "La empresa asociada se encuentra desactivada. Sesión cerrada."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ------------------ módulos ------------------
        modulos = []
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT c.nombre_menu,
                       b.id_empresa_modulo,
                       c.icon
                  FROM dm_sistema.operador_empresa_modulos     a
            INNER JOIN dm_sistema.empresa_modulos           b
                    ON a.id_empresa_modulo = b.id_empresa_modulo
            INNER JOIN dm_sistema.modulos                   c
                    ON b.id_modulo         = c.id_modulo
                 WHERE a.id_operador   = %s
                   AND b.estado        = 1
                   AND c.estado        = 1
                   AND b.id_empresa    = %s
              ORDER BY c.orden;
                """,
                [op.id, op.id_empresa_id],
            )
            for nombre_menu, id_em, icon in cur.fetchall():
                modulos.append(
                    {"nombre_menu": nombre_menu, "id": id_em, "icon": icon}
                )

        # ---------------- funcionalidades -------------
        funcionalidades = []
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT m.id_menu, m.url, m.texto, m.etiqueta, m.descripcion,
                       m.nivel_menu, m.orden, m.modificable, m.separador_up,
                       m.id_modulo
                  FROM dm_sistema.operador                           o
            INNER JOIN dm_sistema.operador_empresa_modulos_menu    oemm
                    ON o.id_operador          = oemm.id_operador
            INNER JOIN dm_sistema.empresa_modulos_menu             emm
                    ON oemm.id_empresa_modulo_menu = emm.id_empresa_modulo_menu
            INNER JOIN dm_sistema.menus                            m
                    ON emm.id_menu            = m.id_menu
                 WHERE o.id_operador = %s;
                """,
                [op.id],
            )
            for row in cur.fetchall():
                funcionalidades.append({
                    "id":           row[0],
                    "url":          row[1],
                    "texto":        row[2],
                    "etiqueta":     row[3],
                    "descripcion":  row[4],
                    "nivel_menu":   row[5],
                    "orden":        row[6],
                    "modificable":  row[7],
                    "separador_up": row[8],
                    "modulo_id":    row[9],
                })

        # --- respuesta + cookie
        resp = Response(
            {
                "message": "Verificación exitosa.",
                "operador":        OperadorSerializer(op).data,
                "modulos":         modulos,
                "funcionalidades": funcionalidades,
            },
            status=status.HTTP_200_OK,
        )
        resp.set_cookie(
            "token",
            sesion_reciente.token,
            httponly=True,
            secure=True,
            max_age=24 * 3600,
            samesite="None",
        )
        return resp

    # ============================================================== #
    # 3) LOGOUT ----------------------------------------------------- #
    # ============================================================== #
    @action(detail=False, methods=["get"])
    def logout(self, request):
        token = request.COOKIES.get("token")
        if not token:
            return Response(
                {"error": "No se encontró la cookie 'token'."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        sesiones = SesionActiva.objects.filter(token=token).order_by("-fecha_registro")
        if not sesiones.exists():
            return Response(
                {"error": "El token de la cookie no coincide con ninguna sesión activa."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # eliminamos TODAS las sesiones que compartan ese token
        sesiones.delete()

        resp = Response({"message": "Sesión eliminada correctamente."},
                        status=status.HTTP_200_OK)
        resp.delete_cookie("token")
        return resp


# ─────────────────────────────────────────────────────────────────────────────
# NUEVO: ViewSet para Proveedores filtrados por la empresa del operador en sesión
# ─────────────────────────────────────────────────────────────────────────────
class ProveedorEmpresaViewSet(RestrictToReactMixin, viewsets.ReadOnlyModelViewSet):
    """
    GET /operadores/ventas/operadores/proveedores-empresa/
    Devuelve los proveedores cuyo id_empresa coincide con la empresa del operador
    obtenido de la cookie 'token'.
    """
    serializer_class = ProveedorSerializer

    def get_queryset(self):
        token = self.request.COOKIES.get("token")
        sesiones = SesionActiva.objects.filter(token=token).order_by("-fecha_registro")
        if not sesiones.exists():
            return Proveedor.objects.none()
        sesion = sesiones.first()
        # id_empresa puede venir de la propia sesión o del operador
        empresa_id = sesion.id_empresa_id or sesion.id_operador.id_empresa_id
        return Proveedor.objects.filter(id_empresa_id=empresa_id)


# ---------------------------------------------------------------------
#  CRUD SIMPLES (sin cambios)
# ---------------------------------------------------------------------
class OperadorBodegaViewSet(RestrictToReactMixin, viewsets.ModelViewSet):
    queryset = OperadorBodega.objects.all()
    serializer_class = OperadorBodegaSerializer


class OperadorEmpresaModuloViewSet(RestrictToReactMixin, viewsets.ModelViewSet):
    queryset = OperadorEmpresaModulo.objects.all()
    serializer_class = OperadorEmpresaModuloSerializer


class OperadorEmpresaModuloMenuViewSet(RestrictToReactMixin, viewsets.ModelViewSet):
    queryset = OperadorEmpresaModuloMenu.objects.all()
    serializer_class = OperadorEmpresaModuloMenuSerializer


class OperadorGrupoViewSet(RestrictToReactMixin, viewsets.ModelViewSet):
    queryset = OperadorGrupo.objects.all()
    serializer_class = OperadorGrupoSerializer


class OperadorPuntoVentaViewSet(RestrictToReactMixin, viewsets.ModelViewSet):
    queryset = OperadorPuntoVenta.objects.all()
    serializer_class = OperadorPuntoVentaSerializer


class SesionViewSet(RestrictToReactMixin, viewsets.ModelViewSet):
    queryset = Sesion.objects.all()
    serializer_class = SesionSerializer


class SesionActivaViewSet(RestrictToReactMixin, viewsets.ModelViewSet):
    queryset = SesionActiva.objects.all()
    serializer_class = SesionActivaSerializer


# ---------------------------------------------------------------------
#  SESIÓN POR TOKEN ----------------------------------------------------
# ---------------------------------------------------------------------
class OperadorByTokenViewSet(RestrictToReactMixin, viewsets.ViewSet):
    """
    Devuelve la sesión activa (post‑2FA) a partir del token almacenado
    en la cookie 'token'.
    """

    def get_by_cookie(self, request):
        token_cookie = request.COOKIES.get("token")
        if not token_cookie:
            return Response(
                {"error": "No se encontró la cookie 'token'."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # -- pueden existir varias filas con el mismo token si el usuario
        #    inició/verificó varias veces; usamos la más reciente y
        #    limpiamos el resto para evitar MultipleObjectsReturned.
        sesiones = (
            SesionActiva.objects
            .select_related("id_operador")
            .filter(token=token_cookie)
            .order_by("-fecha_registro")
        )
        if not sesiones.exists():
            return Response(
                {"error": "El token no coincide con ninguna sesión activa."},
                status=status.HTTP_404_NOT_FOUND,
            )

        sesion_activa = sesiones.first()
        if sesiones.count() > 1:
            sesiones.exclude(id=sesion_activa.id).delete()

        op = sesion_activa.id_operador

        if op.id_empresa.estado != 1:
            sesion_activa.delete()
            return Response(
                {"error": "La empresa asociada al usuario se encuentra desactivada. "
                          "La sesión ha sido cerrada."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ------------------ módulos ------------------
        modulos = []
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT c.nombre_menu,
                       b.id_empresa_modulo,
                       c.icon
                  FROM dm_sistema.operador_empresa_modulos     a
            INNER JOIN dm_sistema.empresa_modulos           b
                    ON a.id_empresa_modulo = b.id_empresa_modulo
            INNER JOIN dm_sistema.modulos                   c
                    ON b.id_modulo         = c.id_modulo
                 WHERE a.id_operador = %s
                   AND b.estado      = 1
                   AND c.estado      = 1
                   AND b.id_empresa  = %s
              ORDER BY c.orden;
                """,
                [op.id, op.id_empresa_id],
            )
            for nombre_menu, id_em, icon in cur.fetchall():
                modulos.append(
                    {"nombre_menu": nombre_menu, "id": id_em, "icon": icon}
                )

        # ---------------- funcionalidades -------------
        funcionalidades = []
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT m.id_menu, m.url, m.texto, m.etiqueta, m.descripcion,
                       m.nivel_menu, m.orden, m.modificable, m.separador_up,
                       m.id_modulo
                  FROM dm_sistema.operador                           o
            INNER JOIN dm_sistema.operador_empresa_modulos_menu    oemm
                    ON o.id_operador          = oemm.id_operador
            INNER JOIN dm_sistema.empresa_modulos_menu             emm
                    ON oemm.id_empresa_modulo_menu = emm.id_empresa_modulo_menu
            INNER JOIN dm_sistema.menus                            m
                    ON emm.id_menu            = m.id_menu
                 WHERE o.id_operador = %s;
                """,
                [op.id],
            )
            for row in cur.fetchall():
                funcionalidades.append({
                    "id":           row[0],
                    "url":          row[1],
                    "texto":        row[2],
                    "etiqueta":     row[3],
                    "descripcion":  row[4],
                    "nivel_menu":   row[5],
                    "orden":        row[6],
                    "modificable":  row[7],
                    "separador_up": row[8],
                    "modulo_id":    row[9],
                })

        return Response(
            {
                "sesion_activa":   SesionActivaSerializer(sesion_activa).data,
                "operador_data":   OperadorSerializer(op).data,
                "modulos":         modulos,
                "funcionalidades": funcionalidades,
            },
            status=status.HTTP_200_OK,
        )