from rest_framework import routers
from django.urls import path, include
from .views import EmpresaViewSet

router = routers.DefaultRouter()
router.register(r'empresa', EmpresaViewSet, basename='empresa')

urlpatterns = [
    path('', include(router.urls)),
]
