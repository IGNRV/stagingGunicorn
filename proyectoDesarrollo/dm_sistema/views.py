# ./dm_sistema/views.py

from __future__ import annotations

import crypt

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Operador
from .serializer import OperadorLoginSerializer


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
        if password_hash and crypt.crypt(password, password_hash) == password_hash:
            return Response(
                {"detail": "Credenciales válidas"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "Credenciales inválidas"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
