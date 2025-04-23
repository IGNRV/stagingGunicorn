from rest_framework.test import APITestCase
from django.urls import reverse
from dm_sistema.models import Operador

class OperadoresAPITest(APITestCase):
    def setUp(self):
        # Crea un operador de prueba; asume que existe Empresa y Grupo con id=1
        self.op = Operador.objects.create(
            username='testuser',
            password=crypt.crypt('secret', crypt.mksalt(crypt.METHOD_SHA256)),
            id_empresa_id=1,
            estado=1
        )

    def test_login_logout_flow(self):
        url_validar = reverse('operadores-validar')
        resp = self.client.post(url_validar, {'username': 'testuser', 'password': 'secret'})
        self.assertEqual(resp.status_code, 200)
        # Debe recibirse la cookie 'token'
        self.assertIn('token', resp.cookies)

        # Ahora logout
        url_logout = reverse('logout')
        self.client.cookies = resp.cookies
        resp2 = self.client.get(url_logout)
        self.assertEqual(resp2.status_code, 200)
