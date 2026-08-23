from datetime import timedelta
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from alunos.models import Aluno
from emprestimos.models import Emprestimo
from livros.models import Livro

# Create your views here.

@login_required
@permission_required("emprestimos.view_emprestimo", raise_exception=True)
def dashboard(request):
    hoje = timezone.localdate()
    inicio = hoje - timedelta(days=6)

    metricas ={
        "titulos": Livro.objects.filter(ativo=True).count(),
        "exemplares": Livro.objects.filter(ativo=True).aggregate(
            total=Coalesce(Sum("quantidade_total"), 0)
        )["total"],
        "disponiveis": Livro.objects.filter(ativo=True).aggregate(
            total=Coalesce(Sum("quantidade_disponivel"), 0)
        )["total"],
        "alunos": Aluno.objects.filter(ativo=True).count(),
        "abertos": Emprestimo.objects.exclude(
            situacao=Emprestimo.Situacao.DEVOLVIDO
        ).count(),
        "atrasados": Emprestimo.objects.filter(
            situacao=Emprestimo.Situacao.ATRASADO
        ).count(),
    }

    recentes = (
        Emprestimo.objects.select_related("aluno", "livro")
        .order_by("-criado_em")[:8]
    )
    proximos = (
        Emprestimo.objects.select_related("aluno", "livro")
        .filter(
            situacao=Emprestimo.Situacao.ATIVO,
            data_prevista__range=(hoje, hoje+timedelta(days=2)),
        )
        .order_by("data_prevista")[:8]
    )

    contagem_por_dia = {
        item["data_inicio"]: item["total"]
        for item in(
            Emprestimo.objects.filter(
                data_inicio__range=(inicio, hoje)
            )
            .values("data_inicio")
            .annotate(total=Count("id"))
        )
    }
    dias = [inicio + timedelta(days=indice) for indice in range(7)]

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "metricas": metricas,
            "recentes": recentes,
            "proximos": proximos,
            "grafico_labels": [dia.strftime("%d/%m") for dia in dias],
            "grafico_valores": [contagem_por_dia.get(dia, 0) for dia in dias],
        },
        )
