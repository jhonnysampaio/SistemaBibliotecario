from .models import Mensagem


def enfileirar_pendencia_ano_letivo(
    *,
    emprestimo,
    ano_destino=None,
):
    aluno = emprestimo.aluno
    if not aluno.email:
        return None

    sufixo = ano_destino or "manual"
    mensagem, _ = Mensagem.objects.get_or_create(
        chave=f"pendencia-anual:{sufixo}:{emprestimo.pk}",
        defaults={
            "tipo": Mensagem.Tipo.PENDENCIA_ANUAL,
            "destinatario": aluno.email,
            "aluno": aluno,
            "emprestimo": emprestimo,
            "assunto": (
                "Solicitação de devolução para encerramento "
                "do ano letivo"
            ),
            "corpo": (
                f"Olá, {aluno.nome}. Solicitamos a devolução do livro "
                f'“{emprestimo.livro.titulo}” para o encerramento '
                "do ano letivo."
            ),
        },
    )
    return mensagem
