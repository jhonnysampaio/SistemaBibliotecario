# importacao/tests.py
import io
from datetime import timedelta
from django.contrib.auth.models import Permission, User
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook
from alunos.models import Aluno
from comunicacoes.models import Mensagem
from importacao.models import ImportacaoPlanilha
from importacao.services.leitor import ErroLeitura, ler_planilha
from importacao.services.validators import verificar_cabecalhos
from livros.models import Categoria, Livro

CABECALHO = "matricula;nome;serie;turma;turno;cpf\n"
LINHA_OK = "00123;Ana Silva;1ª série;A;Matutino;52998224725\n"


def arquivo_csv(texto, nome="alunos.csv"):
    return SimpleUploadedFile(nome, texto.encode("utf-8"), content_type="text/csv")


def arquivo_xlsx(linhas, nome="alunos.xlsx"):
    wb = Workbook()
    for linha in linhas:
        wb.active.append(linha)
    buffer = io.BytesIO()
    wb.save(buffer)
    return SimpleUploadedFile(nome, buffer.getvalue())


class LeitorTests(TestCase):
    def test_csv_preserva_zeros_a_esquerda(self):
        planilha = ler_planilha(arquivo_csv(CABECALHO + LINHA_OK))
        self.assertEqual(planilha.linhas[0]["dados"]["matricula"], "00123")
        self.assertEqual(planilha.linhas[0]["numero"], 2)

    def test_csv_com_virgula_e_bom(self):
        texto = "\ufeffmatricula,nome\n00124,Joao\n"
        planilha = ler_planilha(arquivo_csv(texto))
        self.assertEqual(planilha.linhas[0]["dados"]["nome"], "Joao")

    def test_xlsx_e_csv_geram_a_mesma_estrutura(self):
        x = ler_planilha(arquivo_xlsx([["Matrícula", "Nome"], ["00123", "Ana"]]))
        c = ler_planilha(arquivo_csv("matricula;nome\n00123;Ana\n"))
        self.assertEqual(x.cabecalhos, c.cabecalhos)
        self.assertEqual(x.linhas[0]["dados"], c.linhas[0]["dados"])

    def test_erros_de_arquivo(self):
        for conteudo, nome in [
            ("", "a.csv"),                      # vazio
            ("a;a\n1;2\n", "b.csv"),            # cabecalhos repetidos
            ("x", "c.txt"),                     # extensao nao suportada
            ("matricula;nome\n", "d.csv"),      # sem linhas de dados
        ]:
            with self.assertRaises(ErroLeitura):
                ler_planilha(arquivo_csv(conteudo, nome))


class FluxoAlunosTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("bib", password="x")
        self.usuario.user_permissions.add(Permission.objects.get(codename="add_aluno"))
        self.client.force_login(self.usuario)

    def enviar(self, texto):
        return self.client.post(
            reverse("importacao:enviar", args=["alunos"]),
            {"arquivo": arquivo_csv(texto)},
        )

    def test_upload_nao_grava_alunos(self):
        resposta = self.enviar(CABECALHO + LINHA_OK)
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Aluno.objects.count(), 0)
        self.assertEqual(ImportacaoPlanilha.objects.count(), 1)

    def test_confirmacao_grava_converte_rotulos_e_nao_envia_email(self):
        self.enviar(CABECALHO + LINHA_OK)
        imp = ImportacaoPlanilha.objects.get()
        self.client.post(reverse("importacao:confirmar", args=[imp.pk]))
        aluno = Aluno.objects.get()
        self.assertEqual(
            (aluno.matricula, aluno.serie, aluno.turno, aluno.ativo),
            ("00123", "1º ano", "M", True),
        )
        self.assertEqual(Mensagem.objects.count(), 0)

    def test_linha_invalida_bloqueia_tudo(self):
        self.enviar(CABECALHO + LINHA_OK + "00124;Joao;1ª série;A;Matutino;11111111111\n")
        imp = ImportacaoPlanilha.objects.get()
        self.assertEqual((imp.total_validas, imp.total_invalidas), (1, 1))
        self.client.post(reverse("importacao:confirmar", args=[imp.pk]))
        self.assertEqual(Aluno.objects.count(), 0)

    def test_duplicidade_no_arquivo(self):
        self.enviar(CABECALHO + LINHA_OK + LINHA_OK)
        self.assertEqual(ImportacaoPlanilha.objects.get().total_invalidas, 1)

    def test_nao_repete_importacao_concluida(self):
        self.enviar(CABECALHO + LINHA_OK)
        imp = ImportacaoPlanilha.objects.get()
        url = reverse("importacao:confirmar", args=[imp.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(Aluno.objects.count(), 1)

    def test_get_na_confirmacao_nao_altera(self):
        self.enviar(CABECALHO + LINHA_OK)
        imp = ImportacaoPlanilha.objects.get()
        resposta = self.client.get(reverse("importacao:confirmar", args=[imp.pk]))
        self.assertEqual(resposta.status_code, 405)
        self.assertEqual(Aluno.objects.count(), 0)

    def test_cpf_ja_cadastrado_entre_previa_e_confirmacao_reverte_lote(self):
        self.enviar(CABECALHO + LINHA_OK)
        imp = ImportacaoPlanilha.objects.get()
        Aluno.objects.create(
            matricula="X1", nome="Outro", serie="1º ano", turma="A",
            turno="M", cpf="52998224725",
        )
        self.client.post(reverse("importacao:confirmar", args=[imp.pk]))
        self.assertEqual(Aluno.objects.count(), 1)  # so o que ja existia

    def test_outro_usuario_recebe_404(self):
        self.enviar(CABECALHO + LINHA_OK)
        imp = ImportacaoPlanilha.objects.get()
        intruso = User.objects.create_user("intruso", password="x")
        intruso.user_permissions.add(Permission.objects.get(codename="add_aluno"))
        self.client.force_login(intruso)
        self.assertEqual(
            self.client.get(reverse("importacao:previa", args=[imp.pk])).status_code,
            404,
        )

    def test_sem_permissao_e_anonimo(self):
        sem = User.objects.create_user("sem", password="x")
        self.client.force_login(sem)
        url = reverse("importacao:enviar", args=["alunos"])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)


class FluxoLivrosTests(TestCase):
    CAB = (
        "isbn;titulo;autor;editora;categoria;cdd;local_estante;etiqueta;"
        "quantidade_total\n"
    )

    def setUp(self):
        self.usuario = User.objects.create_user("bib", password="x")
        self.usuario.user_permissions.add(Permission.objects.get(codename="add_livro"))
        self.client.force_login(self.usuario)
        Categoria.objects.create(nome="Literatura")

    def enviar(self, linha):
        self.client.post(
            reverse("importacao:enviar", args=["livros"]),
            {"arquivo": arquivo_csv(self.CAB + linha, "livros.csv")},
        )
        return ImportacaoPlanilha.objects.latest("pk")

    def test_livro_valido_respeita_estoque(self):
        imp = self.enviar(
            "978-0-306-40615-7;Dom Casmurro;Machado;Ed X;literatura;869;A1;E-1;3\n"
        )
        self.client.post(reverse("importacao:confirmar", args=[imp.pk]))
        livro = Livro.objects.get()
        self.assertEqual((livro.quantidade_total, livro.quantidade_disponivel), (3, 3))

    def test_categoria_inexistente_nao_e_criada(self):
        imp = self.enviar("978-0-306-40615-7;Livro;Autor;Ed;Fantasia;869;A1;E-1;3\n")
        self.assertEqual(imp.total_invalidas, 1)
        self.assertFalse(Categoria.objects.filter(nome="Fantasia").exists())

    def test_isbn_invalido_e_quantidade_com_texto(self):
        imp = self.enviar("123;Livro;Autor;Ed;Literatura;869;A1;E-1;tres\n")
        self.assertEqual(imp.total_invalidas, 1)


class CabecalhosTests(TestCase):
    def test_mensagens_de_cabecalho(self):
        erros = verificar_cabecalhos("alunos", ["matricula", "extra"])
        self.assertIn("ausentes: nome", erros[0])
        self.assertIn("não reconhecidas: extra", erros[1])


class LimpezaTests(TestCase):
    def test_comando_expira_previas_vencidas_e_apaga_as_linhas(self):
        usuario = User.objects.create_user("bib", password="x")
        vencida = ImportacaoPlanilha.objects.create(
            usuario=usuario,
            tipo="alunos",
            nome_arquivo="a.csv",
            linhas=[{"numero": 2}],
            expira_em=timezone.now() - timedelta(hours=1),
        )
        em_dia = ImportacaoPlanilha.objects.create(
            usuario=usuario,
            tipo="alunos",
            nome_arquivo="b.csv",
            linhas=[{"numero": 2}],
        )

        call_command("limpar_importacoes", stdout=io.StringIO())
        vencida.refresh_from_db()
        em_dia.refresh_from_db()

        self.assertEqual(vencida.status, ImportacaoPlanilha.Status.EXPIRADA)
        self.assertEqual(vencida.linhas, [])
        self.assertEqual(em_dia.status, ImportacaoPlanilha.Status.VALIDADA)
        self.assertEqual(em_dia.linhas, [{"numero": 2}])


class InterfaceTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("bib", password="x")
        self.usuario.user_permissions.add(*Permission.objects.filter(
            codename__in=["view_livro", "add_livro", "view_aluno", "add_aluno"]
        ))
        self.client.force_login(self.usuario)

    def test_botao_importar_na_lista_de_livros(self):
        resposta = self.client.get(reverse("livros:lista"))
        self.assertContains(
            resposta, reverse("importacao:enviar", args=["livros"])
        )

    def test_botao_importar_na_lista_de_alunos(self):
        resposta = self.client.get(reverse("alunos:lista"))
        self.assertContains(
            resposta, reverse("importacao:enviar", args=["alunos"])
        )

    def test_menu_lateral_tem_link_para_quem_pode_cadastrar(self):
        resposta = self.client.get(reverse("livros:lista"))
        self.assertContains(resposta, reverse("importacao:inicio"))

    def test_quem_so_consulta_nao_ve_botao_nem_link(self):
        leitor = User.objects.create_user("leitor", password="x")
        leitor.user_permissions.add(Permission.objects.get(codename="view_livro"))
        self.client.force_login(leitor)
        resposta = self.client.get(reverse("livros:lista"))
        self.assertNotContains(resposta, "/importacao/")

    def test_cancelar_volta_para_a_lista_do_tipo(self):
        resposta = self.client.get(reverse("importacao:enviar", args=["livros"]))
        self.assertContains(
            resposta,
            'data-voltar="%s"' % reverse("livros:lista"),
        )
        resposta = self.client.get(reverse("importacao:enviar", args=["alunos"]))
        self.assertContains(
            resposta,
            'data-voltar="%s"' % reverse("alunos:lista"),
        )

    def test_tela_inicial_lista_os_dois_tipos(self):
        resposta = self.client.get(reverse("importacao:inicio"))
        self.assertContains(
            resposta, reverse("importacao:enviar", args=["alunos"])
        )
        self.assertContains(
            resposta, reverse("importacao:enviar", args=["livros"])
        )
