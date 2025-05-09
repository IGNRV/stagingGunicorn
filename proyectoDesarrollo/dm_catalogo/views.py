from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import TipoMoneda
from .serializers import TipoMonedaSerializer
from dm_sistema.models import SesionesActivas


# Create your views here.

class TipoMonedaListAPIView(APIView):
    """
    GET /dm_catalogo/tipos-moneda/

    • Requiere la cookie `auth_token`.
    • Devuelve todos los registros de dm_catalogo.tipo_moneda.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        # 1) Verificación de la cookie
        token = request.COOKIES.get("auth_token")
        if not token:
            return Response(
                {"detail": "Token no proporcionado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 2) Buscamos sesión activa
        sesion = (
            SesionesActivas.objects
            .select_related("id_operador", "id_empresa")
            .filter(token=token)
            .first()
        )
        if not sesion:
            return Response(
                {"detail": "Token inválido o sesión expirada"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 3) (Opcional) podrías verificar aquí el estado de la empresa
        empresa = sesion.id_empresa
        if not empresa or getattr(empresa, "estado", 1) != 1:
            return Response(
                {"detail": "La empresa asociada se encuentra inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 4) Listamos todas las monedas
        qs = TipoMoneda.objects.all().order_by("descripcion")
        serializer = TipoMonedaSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
