from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Empresa
from .serializer import EmpresaSerializer
from django.shortcuts import render

# ViewSet para el modelo Empresa que permite listar, crear, actualizar, eliminar
# y obtener datos a partir del id enviado en un POST.
class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer

    @action(detail=False, methods=['post'])
    def obtener_datos(self, request):
        """
        POST /empresa/obtener_datos/
        Recibe en el JSON el campo "id" y retorna los datos de la empresa correspondiente.
        Ejemplo de JSON en el Body:
        {
            "id": 3
        }
        """
        empresa_id = request.data.get("id")
        if not empresa_id:
            return Response(
                {"error": "Falta el campo 'id' en la solicitud."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return Response(
                {"error": "No se encontró la empresa con el id proporcionado."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(empresa)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def cambiar_estado(self, request):
        """
        POST /empresa/cambiar_estado/
        Recibe en el JSON los campos "id" y "estado". Actualiza la columna "estado" de la 
        empresa correspondiente al "id" enviado y retorna la empresa actualizada.
        Ejemplo de JSON en el Body:
        {
            "id": 3,
            "estado": 0
        }
        """
        empresa_id = request.data.get("id")
        nuevo_estado = request.data.get("estado")
        if not empresa_id or nuevo_estado is None:
            return Response(
                {"error": "Se requieren los campos 'id' y 'estado' en la solicitud."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return Response(
                {"error": "No se encontró la empresa con el id proporcionado."},
                status=status.HTTP_404_NOT_FOUND
            )
        empresa.estado = nuevo_estado
        empresa.save()
        serializer = self.get_serializer(empresa)
        return Response(serializer.data, status=status.HTTP_200_OK)
