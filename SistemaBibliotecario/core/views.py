from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from alunos.models import Aluno
from emprestimos.models import Emprestimo
from livros.models import Livro

@login_required
def pesquisa(request):
    q = request.GET.get("q", "").strip()
    alunos = Aluno.objects.none()
    livros = Livro.objects.none()
    emprestimos = Emprestimo.objects.none()

    if len(q) >= 2:
        if request.user.has_perm("alunos.view_aluno"):
            alunos = Aluno.objects.filter(
                Q(nome__icontains=q) 
                | Q(matricula__icontains=q)
            )[:8]
        if request.user.has_perm("livros.view_livro"):
            livros = Livro.objects.select_related("categoria").filter(
                Q(titulo__icontains=q)
                | Q(autor__icontains=q)
                | Q(isbn__icontains=q)
            )[:8]
        if request.user.has_perm("emprestimos.view_emprestimo"):
            emprestimos = Emprestimo.objects.select_related(
                "aluno", "livro"
            ).filter(
                Q(aluno__nome__icontains=q)
                | Q(livro__titulo__icontains=q)
            )[:8]

    return render(
        request,
        "core/pesquisa.html",
        {
            "q": q,
            "alunos": alunos,
            "livros": livros,
            "emprestimos": emprestimos,
        },
    )
