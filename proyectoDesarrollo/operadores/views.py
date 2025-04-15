# ./operadores/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Operador, OperadorBodega, OperadorEmpresaModulo,
    OperadorEmpresaModuloMenu, OperadorGrupo, OperadorPuntoVenta,
    Sesion, SesionActiva
    # Nota: Se ha eliminado el uso de SesionEjecutivo
)
from .serializer import (
    OperadorSerializer, OperadorBodegaSerializer, OperadorEmpresaModuloSerializer,
    OperadorEmpresaModuloMenuSerializer, OperadorGrupoSerializer, OperadorPuntoVentaSerializer,
    SesionSerializer, SesionActivaSerializer
)

import jwt
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
import secrets  # Para generar hashes aleatorios (cod_verificacion)
import requests  # Para enviar el correo replicando la lógica del cURL en PHP
import crypt    # Módulo para verificar el password con BlowFish

from django.db import connection
from django.http import HttpResponseForbidden


class RestrictToReactMixin:
    ALLOWED_ORIGIN = "http://localhost:5173"  # Cambia por el dominio real de tu aplicación React

    def initial(self, request, *args, **kwargs):
        origin = request.META.get("HTTP_ORIGIN")
        if origin != self.ALLOWED_ORIGIN:
            return HttpResponseForbidden("Acceso denegado.")
        return super().initial(request, *args, **kwargs)


def enviar_correo_python(remitente, correo_destino, asunto, detalle):
    """
    Función que replica la lógica del PHP para enviar correo.
    Realiza un POST a http://mail.smartgest.cl/mailserver/server_mail.php
    con los parámetros requeridos.
    """
    data = {
        "destino": correo_destino,
        "asunto": asunto,
        "detalle": detalle,
        "from": remitente
    }
    try:
        resp = requests.post("http://mail.smartgest.cl/mailserver/server_mail.php", data=data)
        # Opcional: se puede revisar resp.status_code, etc.
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


class OperadorViewSet(RestrictToReactMixin, viewsets.ModelViewSet):
    queryset = Operador.objects.all()
    serializer_class = OperadorSerializer

    @action(detail=False, methods=['post'])
    def validar(self, request):
        """
        POST /operadores/operadores/validar/
        Valida que 'operador_id' y 'password' existan en la tabla 'operador'.
        Para la validación se obtiene el operador mediante 'operador_id' y se compara el hash
        almacenado en el campo 'password' con el valor enviado en la solicitud mediante
        crypt.crypt(provided_password, stored_hash) == stored_hash.
        
        Además se verifica lo siguiente:
          - El usuario debe encontrarse activo.
          - La empresa asociada al usuario debe estar activa.
          - El número de conexiones fallidas debe ser menor o igual a 2.
          
        Si alguna de estas condiciones no se cumple, se retorna el error correspondiente.
        Si la validación es correcta:
         - Se reinicia el contador de conexiones fallidas.
         - Se crea una sesión y se genera un token JWT.
         - Se genera y envía un código de verificación por correo.
         - Se retorna un código 200 con el "operador_id".
        """
        operador_id = request.data.get('operador_id')
        password_input = request.data.get('password')
        if not operador_id or not password_input:
            return Response(
                {"error": "Se requieren 'operador_id' y 'password'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si existe un operador con ese ID y si la cuenta está bloqueada.
        try:
            op_temp = Operador.objects.get(operador_id=operador_id)
            if op_temp.conexion_fallida > 3:
                return Response(
                    {"error": "Cuenta bloqueada por demasiados intentos fallidos."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Operador.DoesNotExist:
            pass

        try:
            op = Operador.objects.get(operador_id=operador_id)
            # Validación de estado del usuario, estado de la empresa y conexiones fallidas
            if op.estado != 1:
                return Response(
                    {"error": "El usuario no se encuentra activo."},
                    status=status.HTTP_403_FORBIDDEN
                )
            if op.empresa.estado != 1:
                return Response(
                    {"error": "La empresa asociada al usuario no se encuentra activa."},
                    status=status.HTTP_403_FORBIDDEN
                )
            if op.conexion_fallida > 2:
                return Response(
                    {"error": "El usuario ha superado los intentos de conexión fallidos permitidos (3). Su cuenta ha sido bloqueada."},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Verificar que la contraseña ingresada, al ser encriptada con el mismo salt del password almacenado,
            # coincida con el hash almacenado.
            if crypt.crypt(password_input, op.password) == op.password:
                # Si el login es exitoso, reiniciamos el contador de conexiones fallidas.
                if op.conexion_fallida > 0:
                    op.conexion_fallida = 0
                    op.save()

                response_data = {"operador_id": op.operador_id}

                payload = {
                    'id': op.id,
                    'operador_id': op.operador_id,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }
                token_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

                ip_address = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
                if ',' in ip_address:
                    ip_address = ip_address.split(',')[0].strip()

                nueva_sesion = Sesion.objects.create(
                    ip=ip_address,
                    fecha=timezone.now(),
                    operador_id=op.operador_id,
                    empresa=op.empresa
                )

                random_hash = secrets.token_hex(16)
                SesionActiva.objects.create(
                    operador_id=op.operador_id,
                    sesion_id=str(nueva_sesion.id),
                    fecha_registro=timezone.now(),
                    empresa=op.empresa,
                    token=token_jwt,
                    cod_verificacion=random_hash
                )

                asunto = "Código de Verificación"
                detalle_mail = f"Hola, tu código de verificación es: {random_hash}"
                enviar_correo_python("DM", op.operador_id, asunto, detalle_mail)

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                # Si la contraseña es incorrecta, se incrementa conexion_fallida en 1.
                try:
                    op_incorrecto = Operador.objects.get(operador_id=operador_id)
                    op_incorrecto.conexion_fallida += 1
                    op_incorrecto.save()
                except Operador.DoesNotExist:
                    pass
                return Response(
                    {"error": "No existe un operador con esos datos"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Operador.DoesNotExist:
            return Response(
                {"error": "No existe un operador con esos datos"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def verificar(self, request):
        """
        POST /operadores/operadores/verificar/
        Recibe 'operador_id' y 'cod_verificacion'. Se debe mantener únicamente la
        sesión activa más reciente para ese operador.
        Si el 'cod_verificacion' coincide con la de la sesión más reciente:
         - Se eliminan todas las demás sesiones activas.
         - Se verifica además si el usuario tiene permiso para acceder a la funcionalidad
           'agregar_empresa'.
         - Luego se ejecuta OTRA query (la solicitada) que obtiene las funcionalidades (menus)
           a las que el usuario puede acceder, a partir de su id en la tabla "operador":
           
           SELECT 
               m.id,
               m.url,
               m.texto,
               m.etiqueta,
               m.descripcion,
               m.nivel_menu,
               m.orden,
               m.modificable,
               m.separador_up,
               m.modulo_id
           FROM dm_sistema.operador AS o
           JOIN dm_sistema.operador_empresa_modulos_menu AS oemm
               ON o.id = oemm.operador_id
           JOIN dm_sistema.menus AS m
               ON oemm.empresa_modulo_menu_id = m.id
           JOIN dm_sistema.modulos AS mod
               ON m.modulo_id = mod.id
           WHERE o.id = <VALOR_OPERADOR>;
           
         - Se retorna todo en la respuesta final, junto con la cookie de sesión y el token.
        """
        operador_id = request.data.get('operador_id')
        cod_verificacion = request.data.get('cod_verificacion')
        if not operador_id or not cod_verificacion:
            return Response(
                {"error": "Se requieren 'operador_id' y 'cod_verificacion'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        sesiones = SesionActiva.objects.filter(
            operador_id=operador_id
        ).order_by('-fecha_registro')

        if not sesiones.exists():
            return Response(
                {"error": "No se encontró ninguna sesión activa para este operador."},
                status=status.HTTP_404_NOT_FOUND
            )

        sesion_reciente = sesiones.first()

        if sesion_reciente.cod_verificacion != cod_verificacion:
            return Response(
                {"error": "El código de verificación no coincide con la sesión activa más reciente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        token_jwt = sesion_reciente.token

        # Eliminar todas las demás sesiones activas excepto la más reciente.
        SesionActiva.objects.filter(operador_id=operador_id).exclude(id=sesion_reciente.id).delete()

        try:
            op = Operador.objects.get(operador_id=operador_id)
        except Operador.DoesNotExist:
            return Response(
                {"error": "No se encontró el operador."},
                status=status.HTTP_404_NOT_FOUND
            )

        operator_data = {
            "operador_id": op.operador_id,
            "rut": op.rut,
            "nombres": op.nombres,
            "apellido_paterno": op.apellido_paterno,
            "apellido_materno": op.apellido_materno,
            "modificable": op.modificable,
            "email": op.email,
            "estado": op.estado,
            "acceso_web": op.acceso_web,
            "operador_administrador": op.operador_administrador,
            "grupo": op.grupo.id if op.grupo else None,
            "empresa": op.empresa.id if op.empresa else None,
            "superadmin": op.superadmin,
            "fecha_creacion": op.fecha_creacion
        }

        # Verificar que la empresa asociada al operador siga activa.
        if op.empresa.estado != 1:
            sesion_reciente.delete()
            return Response(
                {"error": "La empresa asociada al usuario se encuentra desactivada. La sesión ha sido cerrada."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Obtener los módulos disponibles para el operador (query antigua).
        modulos = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.nombre_menu, b.id, c.icon
                FROM dm_sistema.operador_empresa_modulos AS a
                JOIN dm_sistema.empresa_modulos AS b ON a.empresa_modulo_id = b.id
                JOIN dm_sistema.modulos AS c ON b.modulo_id = c.id
                WHERE a.operador_id = %s
                  AND b.estado = 1
                  AND c.estado = 1
                  AND b.empresa_id = %s
                ORDER BY c.orden
            """, [op.id, op.empresa.id])
            rows = cursor.fetchall()
            for row in rows:
                modulos.append({
                    "nombre_menu": row[0],
                    "id": row[1],
                    "icon": row[2]
                })

        # Verificar permiso para la funcionalidad 'agregar_empresa'.
        permitir_agregar_empresa = False
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT d.*
                FROM dm_sistema.operador_empresa_modulos_menu a
                JOIN dm_sistema.operador b ON a.operador_id = b.id
                JOIN dm_sistema.empresa_modulos_menu c ON a.empresa_modulo_menu_id = c.id
                JOIN dm_sistema.menus d ON c.menu_id = d.id
                JOIN dm_sistema.empresa_modulos e ON c.empresa_modulo_id = e.id
                WHERE b.id = %s
                  AND d.url = %s
                  AND e.estado = 1
                  AND e.empresa_id = %s
            """, [op.id, 'agregar_empresa', op.empresa.id])
            result_func = cursor.fetchone()
            if result_func is not None:
                permitir_agregar_empresa = True

        # EJECUTAMOS LA NUEVA QUERY SOLICITADA (valida las funcionalidades).
        # <VALOR_OPERADOR> => op.id (PK en la tabla operador).
        funcionalidades = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    m.id,
                    m.url,
                    m.texto,
                    m.etiqueta,
                    m.descripcion,
                    m.nivel_menu,
                    m.orden,
                    m.modificable,
                    m.separador_up,
                    m.modulo_id
                FROM dm_sistema.operador AS o
                JOIN dm_sistema.operador_empresa_modulos_menu AS oemm
                    ON o.id = oemm.operador_id
                JOIN dm_sistema.menus AS m
                    ON oemm.empresa_modulo_menu_id = m.id
                JOIN dm_sistema.modulos AS mod
                    ON m.modulo_id = mod.id
                WHERE o.id = %s
            """, [op.id])
            rows_func = cursor.fetchall()
            for rowf in rows_func:
                funcionalidades.append({
                    "id": rowf[0],
                    "url": rowf[1],
                    "texto": rowf[2],
                    "etiqueta": rowf[3],
                    "descripcion": rowf[4],
                    "nivel_menu": rowf[5],
                    "orden": rowf[6],
                    "modificable": rowf[7],
                    "separador_up": rowf[8],
                    "modulo_id": rowf[9],
                })

        response_data = {
            "message": "Verificación exitosa.",
            "operador": operator_data,
            "modulos": modulos,
            "permitir_agregar_empresa": permitir_agregar_empresa,
            "funcionalidades": funcionalidades
        }
        response = Response(response_data, status=status.HTTP_200_OK)
        response.set_cookie(
            key='token',
            value=token_jwt,
            httponly=True,
            secure=True,
            max_age=24 * 3600,
            samesite='None'
        )
        return response

    @action(detail=False, methods=['get'])
    def logout(self, request):
        """
        GET /operadores/logout/
        Elimina la sesión activa correspondiente al token de la cookie 'token'.
        """
        token_cookie = request.COOKIES.get('token')
        if not token_cookie:
            return Response(
                {"error": "No se encontró la cookie 'token' en la solicitud."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            sesion_activa = SesionActiva.objects.get(token=token_cookie)
        except SesionActiva.DoesNotExist:
            return Response(
                {"error": "El token de la cookie no coincide con ninguna sesión activa."},
                status=status.HTTP_404_NOT_FOUND
            )

        sesion_activa.delete()
        response = Response({"message": "Sesión eliminada correctamente."}, status=status.HTTP_200_OK)
        response.delete_cookie('token')
        return response


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


class OperadorByTokenViewSet(RestrictToReactMixin, viewsets.ViewSet):
    """
    GET /operadores/sesiones-activas-token/
    Obtiene la sesión activa leyendo la cookie 'token'.
    """
    def get_by_cookie(self, request):
        token_cookie = request.COOKIES.get('token')
        if not token_cookie:
            return Response({"error": "No se encontró la cookie 'token' en la solicitud."},
                            status=status.HTTP_401_UNAUTHORIZED)
        try:
            sesion_activa = SesionActiva.objects.get(token=token_cookie)
        except SesionActiva.DoesNotExist:
            return Response({"error": "El token en la cookie no coincide con ninguna sesión activa."},
                            status=status.HTTP_404_NOT_FOUND)

        sesion_activa_data = SesionActivaSerializer(sesion_activa).data

        try:
            op = Operador.objects.get(operador_id=sesion_activa.operador_id)
        except Operador.DoesNotExist:
            return Response(
                {"error": "No se encontró el operador relacionado a esta sesión activa."},
                status=status.HTTP_404_NOT_FOUND
            )

        operador_data = OperadorSerializer(op).data

        # Verificar si la empresa asociada al operador sigue activa.
        if op.empresa.estado != 1:
            sesion_activa.delete()
            return Response({"error": "La empresa asociada al usuario se encuentra desactivada. La sesión ha sido cerrada."},
                            status=status.HTTP_403_FORBIDDEN)

        modulos = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.nombre_menu, b.id, c.icon
                FROM dm_sistema.operador_empresa_modulos AS a
                JOIN dm_sistema.empresa_modulos AS b ON a.empresa_modulo_id = b.id
                JOIN dm_sistema.modulos AS c ON b.modulo_id = c.id
                WHERE a.operador_id = %s
                  AND b.estado = 1
                  AND c.estado = 1
                  AND b.empresa_id = %s
                ORDER BY c.orden
            """, [operador_data['id'], operador_data['empresa']])
            rows = cursor.fetchall()
            for row in rows:
                modulos.append({
                    "nombre_menu": row[0],
                    "id": row[1],
                    "icon": row[2]
                })

        # NUEVA QUERY PARA OBTENER LAS FUNCIONALIDADES DEL OPERADOR
        funcionalidades = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    m.id,
                    m.url,
                    m.texto,
                    m.etiqueta,
                    m.descripcion,
                    m.nivel_menu,
                    m.orden,
                    m.modificable,
                    m.separador_up,
                    m.modulo_id
                FROM dm_sistema.operador AS o
                JOIN dm_sistema.operador_empresa_modulos_menu AS oemm
                    ON o.id = oemm.operador_id
                JOIN dm_sistema.menus AS m
                    ON oemm.empresa_modulo_menu_id = m.id
                JOIN dm_sistema.modulos AS mod
                    ON m.modulo_id = mod.id
                WHERE o.id = %s
            """, [op.id])
            rows_func = cursor.fetchall()
            for rowf in rows_func:
                funcionalidades.append({
                    "id": rowf[0],
                    "url": rowf[1],
                    "texto": rowf[2],
                    "etiqueta": rowf[3],
                    "descripcion": rowf[4],
                    "nivel_menu": rowf[5],
                    "orden": rowf[6],
                    "modificable": rowf[7],
                    "separador_up": rowf[8],
                    "modulo_id": rowf[9],
                })

        combined_data = {
            "sesion_activa": sesion_activa_data,
            "operador_data": operador_data,
            "modulos": modulos,
            "funcionalidades": funcionalidades
        }
        return Response(combined_data, status=status.HTTP_200_OK)
