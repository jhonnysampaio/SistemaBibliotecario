from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import Notificacao
from .services import gerar_alertas_para

# Create your views here.

@login_required
def lista(request):
    gerar_alertas_para(request.user)
    notificacoes = request.user.notificacoes.select_related(
        "emprestimo",
        "emprestimo__aluno",
        "emprestimo__livro",
    )
    pagina = Paginator(notificacoes, 25).get_page(request.GET.get("page"))
    return render (
        request,
        "notificacoes/lista.html",
        {"pagina": pagina },
    )

@require_POST
@login_required
def marcar_lida(request, pk):
    notificacao = get_object_or_404(
        Notificacao,
        pk=pk,
        usuario=request.user,
    )
    notificacao.lida = True
    notificacao.save(update_fields=["lida"])
    return redirect("notificacoes:lista")

@require_POST
@login_required
def marcar_todas_lidas(request):
    request.user.notificacoes.filter(lida=False).update(lida=True)
    return redirect("notificacoes:lista")