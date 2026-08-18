from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AlunoForm
from .models import Aluno


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
