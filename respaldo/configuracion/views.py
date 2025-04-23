# ./configuracion/views.py

from rest_framework import viewsets
from .models import Modulo, Menu, EmpresaModulo, EmpresaModuloMenu
from .serializer import (
    ModuloSerializer,
    MenuSerializer,
    EmpresaModuloSerializer,
    EmpresaModuloMenuSerializer
)

class ModuloViewSet(viewsets.ModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer

class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

class EmpresaModuloViewSet(viewsets.ModelViewSet):
    queryset = EmpresaModulo.objects.all()
    serializer_class = EmpresaModuloSerializer

class EmpresaModuloMenuViewSet(viewsets.ModelViewSet):
    queryset = EmpresaModuloMenu.objects.all()
    serializer_class = EmpresaModuloMenuSerializer
