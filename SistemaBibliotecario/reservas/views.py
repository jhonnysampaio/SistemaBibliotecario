from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ReservaForm
from .models import Reserva
from .services import (
    RegraReservaError,
    cancelar_reserva,
    criar_reserva,
    posicao_fila,
)


@login_required
@permission_required("reservas.view_reserva", raise_exception=True)
def lista(request):
    reservas = Reserva.objects.select_related("aluno", "livro")
    status = request.GET.get("status", "")
    if status in Reserva.Status.values:
        reservas = reservas.filter(status=status)

    pagina = Paginator(reservas, 20).get_page(request.GET.get("page"))
    for reserva in pagina.object_list:
        reserva.posicao = posicao_fila(reserva)

    parametros = request.GET.copy()
    parametros.pop("page", None)
    return render(
        request,
        "reservas/lista.html",
        {
            "pagina": pagina,
            "status": status,
            "status_opcoes": Reserva.Status.choices,
            "querystring": parametros.urlencode(),
        },
    )


@login_required
@permission_required("reservas.add_reserva", raise_exception=True)
def nova(request):
    form = ReservaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            criar_reserva(**form.cleaned_data)
        except RegraReservaError as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, "Reserva adicionada à fila.")
            return redirect("reservas:lista")

    return render(request, "reservas/form.html", {"form": form})


@login_required
@require_POST
@permission_required("reservas.change_reserva", raise_exception=True)
def cancelar(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    try:
        cancelar_reserva(reserva=reserva)
    except RegraReservaError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Reserva cancelada.")
    return redirect("reservas:lista")
