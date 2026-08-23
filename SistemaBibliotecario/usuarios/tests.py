from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AutenticacaoHomologacaoTests(TestCase):
    senha_original = "senha-forte-123"

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario-ativo",
            password=self.senha_original,
        )
        self.inativo = User.objects.create_user(
            username="usuario-inativo",
            password=self.senha_original,
            is_active=False,
        )

    def test_usuario_anonimo_e_redirecionado_para_login(self):
        destino = reverse("dashboard:inicio")

        response = self.client.get(destino)

        self.assertRedirects(
            response,
            f'{reverse("usuarios:login")}?next={destino}',
        )

    def test_senha_incorreta_nao_autentica(self):
        response = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.usuario.username,
                "password": "senha-incorreta",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_usuario_inativo_nao_autentica(self):
        response = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.inativo.username,
                "password": self.senha_original,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_por_post_encerra_sessao(self):
        self.client.force_login(self.usuario)

        response = self.client.post(reverse("usuarios:logout"))

        self.assertRedirects(response, reverse("usuarios:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_alteracao_de_senha_mantem_sessao(self):
        self.client.force_login(self.usuario)
        nova_senha = "nova-senha-segura-456"

        response = self.client.post(
            reverse("usuarios:alterar_senha"),
            {
                "old_password": self.senha_original,
                "new_password1": nova_senha,
                "new_password2": nova_senha,
            },
        )

        self.assertRedirects(response, reverse("usuarios:perfil"))
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            self.usuario.pk,
        )
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(nova_senha))
