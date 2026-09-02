from django.db import transaction
from django.template.loader import render_to_string

from .envio import enviar_mensagem_por_id
from .models import Mensagem


def _renderizar_corpo_html(
    *,
    pre_cabecalho,
    categoria,
    titulo,
    nome_aluno,
    texto,
    detalhes,
    destaque_titulo,
    destaque_texto,
    tom="padrao",
):
    return render_to_string(
        "comunicacoes/email/mensagem.html",
        {
            "pre_cabecalho": pre_cabecalho,
            "categoria": categoria,
            "titulo": titulo,
            "nome_aluno": nome_aluno,
            "texto": texto,
            "detalhes": detalhes,
            "destaque_titulo": destaque_titulo,
            "destaque_texto": destaque_texto,
            "tom": tom,
        },
    )


def _agendar_envio_imediato(*, mensagem, criada):
    if criada:
        transaction.on_commit(
            lambda mensagem_id=mensagem.pk: enviar_mensagem_por_id(
                mensagem_id
            )
        )


def enfileirar_cadastro_aluno(*, aluno):
    if not aluno.email:
        return None

    mensagem, criada = Mensagem.objects.get_or_create(
        chave=f"cadastro-aluno:{aluno.pk}",
        defaults={
            "tipo": Mensagem.Tipo.CADASTRO,
            "destinatario": aluno.email,
            "aluno": aluno,
            "assunto": "Cadastro realizado no Sistema Bibliotecário",
            "corpo": (
                f"Olá, {aluno.nome}. Seu cadastro foi realizado no "
                "Sistema Bibliotecário. "
                f"Matrícula: {aluno.matricula}. "
                f"Turma: {aluno.serie} {aluno.turma} - "
                f"{aluno.get_turno_display()}. "
                "Este endereço receberá avisos sobre empréstimos e reservas."
            ),
            "corpo_html": _renderizar_corpo_html(
                pre_cabecalho=(
                    "Seu cadastro no Sistema Bibliotecário foi confirmado."
                ),
                categoria="Cadastro confirmado",
                titulo="Bem-vindo à biblioteca",
                nome_aluno=aluno.nome,
                texto=(
                    "Seu cadastro foi realizado com sucesso. A partir de "
                    "agora, este endereço receberá avisos importantes da "
                    "biblioteca."
                ),
                detalhes=(
                    {"rotulo": "Matrícula", "valor": aluno.matricula},
                    {
                        "rotulo": "Turma",
                        "valor": f"{aluno.serie} {aluno.turma}",
                    },
                    {
                        "rotulo": "Turno",
                        "valor": aluno.get_turno_display(),
                    },
                ),
                destaque_titulo="Você receberá lembretes por aqui",
                destaque_texto=(
                    "Enviaremos confirmações de empréstimos, avisos de "
                    "devolução e notificações de reservas."
                ),
            ),
        },
    )
    _agendar_envio_imediato(mensagem=mensagem, criada=criada)
    return mensagem


def enfileirar_emprestimo_realizado(*, emprestimo):
    aluno = emprestimo.aluno
    if not aluno.email:
        return None

    mensagem, criada = Mensagem.objects.get_or_create(
        chave=f"emprestimo:{emprestimo.pk}:realizado",
        defaults={
            "tipo": Mensagem.Tipo.EMPRESTIMO,
            "destinatario": aluno.email,
            "aluno": aluno,
            "emprestimo": emprestimo,
            "assunto": "Empréstimo realizado",
            "corpo": (
                f"Olá, {aluno.nome}. O empréstimo do livro "
                f"“{emprestimo.livro.titulo}” foi realizado em "
                f"{emprestimo.data_inicio:%d/%m/%Y}. "
                "A devolução está prevista para "
                f"{emprestimo.data_prevista:%d/%m/%Y}."
            ),
            "corpo_html": _renderizar_corpo_html(
                pre_cabecalho=(
                    "Empréstimo registrado. Confira a data de devolução."
                ),
                categoria="Empréstimo registrado",
                titulo="Boa leitura!",
                nome_aluno=aluno.nome,
                texto=(
                    "O empréstimo abaixo foi registrado no Sistema "
                    "Bibliotecário."
                ),
                detalhes=(
                    {
                        "rotulo": "Livro",
                        "valor": emprestimo.livro.titulo,
                    },
                    {
                        "rotulo": "Retirada",
                        "valor": f"{emprestimo.data_inicio:%d/%m/%Y}",
                    },
                    {
                        "rotulo": "Devolução prevista",
                        "valor": f"{emprestimo.data_prevista:%d/%m/%Y}",
                    },
                ),
                destaque_titulo="Lembrete",
                destaque_texto=(
                    "Guarde a data de devolução para que outras pessoas "
                    "também possam aproveitar esta leitura."
                ),
            ),
        },
    )
    _agendar_envio_imediato(mensagem=mensagem, criada=criada)
    return mensagem


def enfileirar_prazo_emprestimo(*, emprestimo):
    aluno = emprestimo.aluno
    if not aluno.email:
        return None

    mensagem, criada = Mensagem.objects.get_or_create(
        chave=(
            f"prazo:{emprestimo.pk}:"
            f"{emprestimo.data_prevista.isoformat()}"
        ),
        defaults={
            "tipo": Mensagem.Tipo.PRAZO,
            "destinatario": aluno.email,
            "aluno": aluno,
            "emprestimo": emprestimo,
            "assunto": "Prazo de devolução próximo",
            "corpo": (
                f"Olá, {aluno.nome}. O prazo para devolver o livro "
                f"“{emprestimo.livro.titulo}” está próximo. "
                "A devolução deve ser realizada até "
                f"{emprestimo.data_prevista:%d/%m/%Y}."
            ),
            "corpo_html": _renderizar_corpo_html(
                pre_cabecalho=(
                    "A data de devolução do seu empréstimo está próxima."
                ),
                categoria="Devolução próxima",
                titulo="O prazo está chegando",
                nome_aluno=aluno.nome,
                texto=(
                    "Este é um lembrete para você se organizar e devolver "
                    "o livro dentro do prazo."
                ),
                detalhes=(
                    {
                        "rotulo": "Livro",
                        "valor": emprestimo.livro.titulo,
                    },
                    {
                        "rotulo": "Devolução prevista",
                        "valor": f"{emprestimo.data_prevista:%d/%m/%Y}",
                    },
                ),
                destaque_titulo="Organize a devolução",
                destaque_texto=(
                    "Entregue o exemplar na biblioteca até a data indicada "
                    "para evitar pendências."
                ),
                tom="aviso",
            ),
        },
    )
    _agendar_envio_imediato(mensagem=mensagem, criada=criada)
    return mensagem


def enfileirar_atraso(*, emprestimo):
    aluno = emprestimo.aluno
    if not aluno.email:
        return None

    mensagem, criada = Mensagem.objects.get_or_create(
        chave=(
            f"atraso:{emprestimo.pk}:"
            f"{emprestimo.data_prevista.isoformat()}"
        ),
        defaults={
            "tipo": Mensagem.Tipo.ATRASO,
            "destinatario": aluno.email,
            "aluno": aluno,
            "emprestimo": emprestimo,
            "assunto": "Livro com devolução em atraso",
            "corpo": (
                f"Olá, {aluno.nome}. O livro “{emprestimo.livro.titulo}” "
                "deveria ter sido devolvido em "
                f"{emprestimo.data_prevista:%d/%m/%Y}."
            ),
            "corpo_html": _renderizar_corpo_html(
                pre_cabecalho=(
                    "Há um empréstimo com devolução em atraso."
                ),
                categoria="Devolução em atraso",
                titulo="Precisamos da sua atenção",
                nome_aluno=aluno.nome,
                texto=(
                    "Identificamos que o prazo de devolução do exemplar "
                    "abaixo já terminou."
                ),
                detalhes=(
                    {
                        "rotulo": "Livro",
                        "valor": emprestimo.livro.titulo,
                    },
                    {
                        "rotulo": "Data prevista",
                        "valor": f"{emprestimo.data_prevista:%d/%m/%Y}",
                    },
                ),
                destaque_titulo="Regularize a pendência",
                destaque_texto=(
                    "Por favor, devolva o livro à biblioteca assim que "
                    "possível."
                ),
                tom="perigo",
            ),
        },
    )
    _agendar_envio_imediato(mensagem=mensagem, criada=criada)
    return mensagem


def enfileirar_reserva_disponivel(*, reserva):
    if not reserva.aluno.email:
        return None

    mensagem, criada = Mensagem.objects.get_or_create(
        chave=f"reserva:{reserva.pk}:disponivel",
        defaults={
            "tipo": Mensagem.Tipo.RESERVA,
            "destinatario": reserva.aluno.email,
            "aluno": reserva.aluno,
            "reserva": reserva,
            "assunto": "Livro reservado disponível",
            "corpo": (
                f"Olá, {reserva.aluno.nome}. O livro "
                f"“{reserva.livro.titulo}” está disponível até "
                f"{reserva.disponivel_ate:%d/%m/%Y %H:%M}."
            ),
            "corpo_html": _renderizar_corpo_html(
                pre_cabecalho="O livro que você reservou está disponível.",
                categoria="Reserva disponível",
                titulo="Seu livro está esperando",
                nome_aluno=reserva.aluno.nome,
                texto=(
                    "O exemplar reservado já pode ser retirado na "
                    "biblioteca."
                ),
                detalhes=(
                    {
                        "rotulo": "Livro",
                        "valor": reserva.livro.titulo,
                    },
                    {
                        "rotulo": "Disponível até",
                        "valor": f"{reserva.disponivel_ate:%d/%m/%Y %H:%M}",
                    },
                ),
                destaque_titulo="Retire dentro do prazo",
                destaque_texto=(
                    "Após a data indicada, a reserva poderá ser liberada "
                    "para a próxima pessoa da fila."
                ),
                tom="sucesso",
            ),
        },
    )
    _agendar_envio_imediato(mensagem=mensagem, criada=criada)
    return mensagem


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
            "corpo_html": _renderizar_corpo_html(
                pre_cabecalho=(
                    "Há uma devolução pendente para o encerramento do ano."
                ),
                categoria="Pendência do ano letivo",
                titulo="Solicitação de devolução",
                nome_aluno=aluno.nome,
                texto=(
                    "Para concluirmos a atualização do ano letivo, "
                    "precisamos que o exemplar abaixo seja devolvido."
                ),
                detalhes=(
                    {
                        "rotulo": "Livro",
                        "valor": emprestimo.livro.titulo,
                    },
                    {
                        "rotulo": "Devolução prevista",
                        "valor": f"{emprestimo.data_prevista:%d/%m/%Y}",
                    },
                ),
                destaque_titulo="Resolva esta pendência",
                destaque_texto=(
                    "Entregue o livro na biblioteca antes do encerramento "
                    "do ano letivo."
                ),
                tom="perigo",
            ),
        },
    )
    return mensagem
