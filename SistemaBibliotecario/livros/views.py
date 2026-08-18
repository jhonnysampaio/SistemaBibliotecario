from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CategoriaForm, LivroForm
from .models import Categoria, Livro


@login_required
@permission_required("livros.view_livro", raise_exception=True)
def lista(request):
    q = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "")
    disponibilidade = request.GET.get("disponibilidade", "")

    livros = Livro.objects.select_related("categoria")

    if q:
        livros = livros.filter(
            Q(titulo__icontains=q)
            | Q(autor__icontains=q)
            | Q(isbn__icontains=q)
            | Q(etiqueta__icontains=q)
        )

    if categoria_id:
        livros = livros.filter(categoria_id=categoria_id)

    if disponibilidade == "disponiveis":
        livros = livros.filter(quantidade_disponivel__gt=0, ativo=True)
    elif disponibilidade == "indisponiveis":
        livros = livros.filter(quantidade_disponivel=0)

    pagina = Paginator(livros, 20).get_page(request.GET.get("page"))
    parametros = request.GET.copy()
    parametros.pop("page", None)

    return render(
        request,
        "livros/lista.html",
        {
            "pagina": pagina,
            "categorias": Categoria.objects.filter(ativa=True),
            "q": q,
            "categoria_id": categoria_id,
            "disponibilidade": disponibilidade,
            "querystring": parametros.urlencode(),
        },
    )


@login_required
@permission_required("livros.view_livro", raise_exception=True)
def detalhe(request, pk):
    livro = get_object_or_404(
        Livro.objects.select_related("categoria").prefetch_related(
            "emprestimos__aluno"
        ),
        pk=pk,
    )
    return render(request, "livros/detalhe.html", {"livro": livro})


@login_required
@permission_required("livros.add_livro", raise_exception=True)
def criar(request):
    form = LivroForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        livro = form.save()
        messages.success(request, "Livro cadastrado.")
        return redirect("livros:detalhe", pk=livro.pk)

    return render(
        request,
        "livros/form.html",
        {"form": form, "titulo": "Novo livro"},
    )


@login_required
@permission_required("livros.change_livro", raise_exception=True)
def editar(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    form = LivroForm(request.POST or None, instance=livro)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request,
            "Livro atualizado sem alterar empréstimos abertos.",
        )
        return redirect("livros:detalhe", pk=livro.pk)

    return render(
        request,
        "livros/form.html",
        {"form": form, "titulo": "Editar livro"},
    )


@login_required
@require_POST
@permission_required("livros.delete_livro", raise_exception=True)
def excluir(request, pk):
    livro = get_object_or_404(Livro, pk=pk)

    try:
        livro.delete()
        messages.success(request, "Livro excluído.")
    except ProtectedError:
        messages.error(
            request,
            "Há empréstimos vinculados. Desative o livro para preservar o histórico.",
        )

    return redirect("livros:lista")


@login_required
@permission_required("livros.view_categoria", raise_exception=True)
def categorias(request):
    form = CategoriaForm(request.POST or None)

    if request.method == "POST":
        if not request.user.has_perm("livros.add_categoria"):
            raise PermissionDenied

        if form.is_valid():
            form.save()
            messages.success(request, "Categoria criada.")
            return redirect("livros:categorias")

    return render(
        request,
        "livros/categorias.html",
        {"form": form, "categorias": Categoria.objects.all()},
    )
