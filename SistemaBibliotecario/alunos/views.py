from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from comunicacoes.services import enfileirar_pendencia_ano_letivo
from emprestimos.models import Emprestimo

from .forms import AlunoForm, FechamentoAnoLetivoForm
from .models import Aluno
from .services_ano_letivo import fechar_ano_letivo


@login_required
@permission_required("alunos.view_aluno", raise_exception=True)
def lista(request):
    q = request.GET.get("q", "").strip()
    situacao = request.GET.get("situacao", "")
    alunos = Aluno.objects.all()

    if q:
        alunos = alunos.filter(
            Q(nome__icontains=q)
            | Q(matricula__icontains=q)
            | Q(cpf__icontains=q)
        )

    if situacao == "ativos":
        alunos = alunos.filter(ativo=True)
    elif situacao == "inativos":
        alunos = alunos.filter(ativo=False)

    pagina = Paginator(alunos, 20).get_page(request.GET.get("page"))
    parametros = request.GET.copy()
    parametros.pop("page", None)
    return render(
        request,
        "alunos/lista.html",
        {
            "pagina": pagina,
            "q": q,
            "situacao": situacao,
            "querystring": parametros.urlencode(),
        },
    )


@login_required
@permission_required("alunos.view_aluno", raise_exception=True)
def detalhe(request, pk):
    aluno = get_object_or_404(
        Aluno.objects.prefetch_related("emprestimos__livro"),
        pk=pk,
    )
    return render(request, "alunos/detalhe.html", {"aluno": aluno})


@login_required
@permission_required("alunos.add_aluno", raise_exception=True)
def criar(request):
    form = AlunoForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        aluno = form.save()
        messages.success(request, "Aluno cadastrado.")
        return redirect("alunos:detalhe", pk=aluno.pk)

    return render(
        request,
        "alunos/form.html",
        {"form": form, "titulo": "Novo aluno"},
    )


@login_required
@permission_required("alunos.change_aluno", raise_exception=True)
def editar(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    form = AlunoForm(request.POST or None, instance=aluno)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Aluno atualizado.")
        return redirect("alunos:detalhe", pk=aluno.pk)

    return render(
        request,
        "alunos/form.html",
        {"form": form, "titulo": "Editar aluno"},
    )


@login_required
@require_POST
@permission_required("alunos.delete_aluno", raise_exception=True)
def excluir(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)

    try:
        aluno.delete()
        messages.success(request, "Aluno excluído.")
    except ProtectedError:
        messages.error(
            request,
            "O aluno possui histórico. Desative o cadastro em vez de excluí-lo.",
        )

    return redirect("alunos:lista")


@login_required
@permission_required("alunos.change_aluno", raise_exception=True)
def fechamento_ano_letivo(request):
    pendencias = (
        Emprestimo.objects.exclude(situacao=Emprestimo.Situacao.DEVOLVIDO)
        .select_related("aluno", "livro")
        .order_by("aluno__nome", "data_prevista")
    )
    form = FechamentoAnoLetivoForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        resultado = fechar_ano_letivo(
            ano_destino=form.cleaned_data["ano_destino"],
            usuario=request.user,
        )
        messages.success(
            request,
            f"{len(resultado.atualizados)} aluno(s) atualizado(s).",
        )
        return redirect("alunos:fechamento_ano_letivo")

    return render(
        request,
        "alunos/fechamento_ano_letivo.html",
        {"form": form, "pendencias": pendencias},
    )


@login_required
@require_POST
@permission_required(
    ("emprestimos.view_emprestimo", "alunos.change_aluno"),
    raise_exception=True,
)
def solicitar_devolucao(request, pk):
    emprestimo = get_object_or_404(
        Emprestimo.objects.exclude(
            situacao=Emprestimo.Situacao.DEVOLVIDO
        ).select_related("aluno", "livro"),
        pk=pk,
    )
    mensagem = enfileirar_pendencia_ano_letivo(
        emprestimo=emprestimo
    )
    if mensagem is None:
        messages.error(
            request,
            "O aluno não possui e-mail cadastrado.",
        )
    else:
        messages.success(
            request,
            "Solicitação adicionada à fila de envio.",
        )
    return redirect("alunos:fechamento_ano_letivo")
