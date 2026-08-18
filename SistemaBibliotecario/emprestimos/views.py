from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import EmprestimoForm
from .models import Emprestimo
from .services import (
    RegraEmprestimoError,
    atualizar_atrasos,
    devolver_emprestimo,
    registrar_emprestimo,
    renovar_emprestimo,
)


@permission_required("emprestimos.view_emprestimo", raise_exception=True)
def lista(request):
    atualizar_atrasos()
    q = request.GET.get("q", "").strip()
    situacao = request.GET.get("situacao", "abertos")
    emprestimos = Emprestimo.objects.select_related("aluno", "livro")

    if q:
        emprestimos = emprestimos.filter(
            Q(aluno__nome__icontains=q)
            | Q(aluno__matricula__icontains=q)
            | Q(livro__titulo__icontains=q)
        )
    if situacao == "abertos":
        emprestimos = emprestimos.exclude(
            situacao=Emprestimo.Situacao.DEVOLVIDO
        )
    elif situacao in Emprestimo.Situacao.values:
        emprestimos = emprestimos.filter(situacao=situacao)

    pagina = Paginator(emprestimos, 20).get_page(request.GET.get("page"))
    parametros = request.GET.copy()
    parametros.pop("page", None)

    return render(
        request,
        "emprestimos/lista.html",
        {
            "pagina": pagina,
            "q": q,
            "situacao": situacao,
            "querystring": parametros.urlencode(),
        },
    )


@permission_required("emprestimos.view_emprestimo", raise_exception=True)
def detalhe(request, pk):
    emprestimo = get_object_or_404(
        Emprestimo.objects.select_related("aluno", "livro", "registrado_por"),
        pk=pk,
    )
    return render(
        request,
        "emprestimos/detalhe.html",
        {"emprestimo": emprestimo},
    )


@permission_required("emprestimos.add_emprestimo", raise_exception=True)
def novo(request):
    form = EmprestimoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            emprestimo = registrar_emprestimo(
                aluno=form.cleaned_data["aluno"],
                livro=form.cleaned_data["livro"],
                data_prevista=form.cleaned_data["data_prevista"],
                observacoes=form.cleaned_data["observacoes"],
                usuario=request.user,
            )
        except RegraEmprestimoError as error:
            form.add_error(None, str(error))
        else:
            messages.success(
                request,
                "Empréstimo registrado e estoque atualizado.",
            )
            return redirect("emprestimos:detalhe", pk=emprestimo.pk)

    return render(request, "emprestimos/novo.html", {"form": form})


@require_POST
@permission_required(
    "emprestimos.pode_devolver_emprestimo",
    raise_exception=True,
)
def devolver(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    try:
        devolver_emprestimo(emprestimo=emprestimo)
        messages.success(request, "Devolução registrada.")
    except RegraEmprestimoError as error:
        messages.error(request, str(error))
    return redirect("emprestimos:detalhe", pk=pk)


@require_POST
@permission_required(
    "emprestimos.pode_renovar_emprestimo",
    raise_exception=True,
)
def renovar(request, pk):
    emprestimo = get_object_or_404(Emprestimo, pk=pk)
    try:
        renovar_emprestimo(emprestimo=emprestimo)
        messages.success(request, "Empréstimo renovado por sete dias.")
    except RegraEmprestimoError as error:
        messages.error(request, str(error))
    return redirect("emprestimos:detalhe", pk=pk)


@permission_required("emprestimos.view_emprestimo", raise_exception=True)
def historico(request):
    emprestimos = (
        Emprestimo.objects.select_related("aluno", "livro")
        .filter(situacao=Emprestimo.Situacao.DEVOLVIDO)
    )
    pagina = Paginator(emprestimos, 25).get_page(request.GET.get("page"))
    parametros = request.GET.copy()
    parametros.pop("page", None)

    return render(
        request,
        "emprestimos/historico.html",
        {
            "pagina": pagina,
            "querystring": parametros.urlencode(),
        },
    )
