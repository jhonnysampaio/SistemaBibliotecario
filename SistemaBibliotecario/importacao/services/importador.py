from pathlib import Path
from django.db import IntegrityError, transaction
from django.utils import timezone
from importacao.models import ImportacaoPlanilha
from .leitor import ErroLeitura, ler_planilha
from .validators import (FORMULARIOS, _erros_do_formulario, validar_linhas,
                           verificar_cabecalhos)

class ImportacaoNaoPermitida(Exception):
    """Importacao ja processada, expirada ou com linhas invalidas"""

class LinhaRejeitada(Exception):
    def __init__(self, numero, erros):
        self.numero = numero
        self.erros = erros
        super().__init__("Linha %s rejeitada: %s" % (numero, "; ".join(erros)))

def criar_previa(*, usuario, tipo, arquivo):
    """Le e valida. Nao grava alunos/livros: so cria o registro da previa"""
    planilha = ler_planilha(arquivo)
    problemas = verificar_cabecalhos(tipo, planilha.cabecalhos)

    if problemas:
        raise ErroLeitura(" ".join(problemas))

    linhas = validar_linhas(tipo, planilha)
    validas = sum(1 for l in linhas if l["valida"])

    return ImportacaoPlanilha.objects.create(
        usuario=usuario,
        tipo=tipo,
        nome_arquivo=Path(arquivo.name).name[:120],
        linhas=linhas,
        total_linhas=len(linhas),
        total_validas=validas,
        total_invalidas=len(linhas) - validas,
    )

def confirmar_importacao(*, importacao_id, usuario):
    """Revalida e grava tudo em uma unica transacao (tudo ou nada)."""
    try:
        with transaction.atomic():
            importacao = (
                ImportacaoPlanilha.objects.select_for_update()
                .get(pk=importacao_id, usuario=usuario)
            )
            if importacao.status != ImportacaoPlanilha.Status.VALIDADA:
                raise ImportacaoNaoPermitida("Esta importação já foi processada.")
            if importacao.expirada:
                raise ImportacaoNaoPermitida("A prévia expirou. Envie a planilha novamente.")
            if importacao.total_invalidas:
                raise ImportacaoNaoPermitida(
                    "Existem linhas inválidas. Corrija a planilha e envie novamente."
                )
            formulario = FORMULARIOS[importacao.tipo]

            for linha in importacao.linhas:
                form = formulario(linha["dados"])    # revalida contra o banco de agora

                if not form.is_valid():
                    raise LinhaRejeitada(linha["numero"], _erros_do_formulario(form))
                form.save()    # AlunoForm -> Aluno.save(); LivroForm -> salvar_livro_com_estoque

            importacao.total_importadas = len(importacao.linhas)
            importacao.status = ImportacaoPlanilha.Status.CONCLUIDA
            importacao.concluido_em = timezone.now()
            importacao.linhas = []   # apaga dados pessoais temporarios
            importacao.save()
    except IntegrityError:
        raise LinhaRejeitada(None, ["Conflito de unicidade detectado durante a gravacao."])
    return importacao