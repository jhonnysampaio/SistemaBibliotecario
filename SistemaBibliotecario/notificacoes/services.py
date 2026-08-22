from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from emprestimos.models import Emprestimo
from emprestimos.services import atualizar_atrasos
from .models import Notificacao

def gerar_alertas_para(usuario):
    if not usuario.has_perm("emprestimos.view_emprestimo"):
        return
    atualizar_atrasos()
    hoje = timezone.localdate()
    limite = hoje + timedelta(days=2)
    do_usuario = Q(registrado_por=usuario)  | Q(registrado_por__isnull=True)

    proximos = Emprestimo.objects.filter(
        do_usuario,
        situacao=Emprestimo.Situacao.ATIVO,
        data_prevista__range=(hoje,limite),
    ).select_related("aluno", "livro")

    atrasados = Emprestimo.objects.filter(
        do_usuario,
        situacao=Emprestimo.Situacao.ATRASADO,
    ).select_related("aluno", "livro")

    for emprestimo in proximos:
        Notificacao.objects.get_or_create(
            usuario=usuario,
            emprestimo=emprestimo,
            tipo=Notificacao.Tipo.PRAZO,
            defaults={
                "titulo": "Devolução próxima",
                "mensagem": (
                    f"{emprestimo.aluno.nome} deve devolver "
                    f'“{emprestimo.livro.titulo}” até '
                    f"{emprestimo.data_prevista:%d/%m/%Y}."
                ),
            },
        )

    for emprestimo in atrasados:
        Notificacao.objects.get_or_create(
            usuario=usuario,
            emprestimo=emprestimo,
            tipo=Notificacao.Tipo.ATRASO,
            defaults={
                "titulo": "Empréstimo atrasado",
                "mensagem": (
                    f"{emprestimo.aluno.nome} está com "
                    f'“{emprestimo.livro.titulo}” em atraso.'
                ),
            },
        )

    Notificacao.objects.filter(
        usuario=usuario,
        lida=False,
        emprestimo__situacao=Emprestimo.Situacao.DEVOLVIDO,
    ).update(lida=True)
