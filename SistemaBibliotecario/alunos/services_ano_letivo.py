from dataclasses import dataclass, field
from django.db import transaction
from emprestimos.models import Emprestimo
from .models import Aluno, HistoricoProgressao

SERIE_SEGUINTE = {
    "1º ano": "2º ano",
    "2º ano": "3º ano",
    "3º ano": None,
}

@dataclass
class ResultadoFechamento:
    atualizados: list = field(default_factory=list)
    pendentes: list = field(default_factory=list)
    revisar: list = field(default_factory=list)

def ids_com_pendencia():
    return set(
        Emprestimo.objects.exclude(
            situacao=Emprestimo.Situacao.DEVOLVIDO
        ).values_list("aluno_id", flat=True)
    )
@transaction.atomic
def fechar_ano_letivo(*, ano_destino, usuario):
    resultado = ResultadoFechamento()
    pendentes = ids_com_pendencia()
    alunos = Aluno.objects.select_for_update().filter(ativo=True)

    for aluno in alunos:
        if aluno.pk in pendentes:
            resultado.pendentes.append(aluno)
            continue
        if HistoricoProgressao.objects.filter(
            aluno=aluno, ano_destino=ano_destino
        ).exists():
            continue
        if aluno.serie not in SERIE_SEGUINTE:
            resultado.revisar.append(aluno)
            continue

        ano_origem = aluno.ano_letivo
        serie_anterior = aluno.serie
        serie_nova = SERIE_SEGUINTE[serie_anterior]
        concluido = serie_nova is None
        if concluido:
            aluno.ativo = False
        else:
            aluno.serie = serie_nova
        aluno.ano_letivo = ano_destino
        aluno.save(update_fields=["serie", "ano_letivo", "ativo", "atualizado_em"])
        HistoricoProgressao.objects.create(
            aluno=aluno,
            ano_origem=ano_origem,
            ano_destino=ano_destino,
            serie_anterior=serie_anterior,
            serie_nova=serie_nova or "",
            concluido=concluido,
            registrado_por=usuario,
        )
        resultado.atualizados.append(aluno)
    return resultado