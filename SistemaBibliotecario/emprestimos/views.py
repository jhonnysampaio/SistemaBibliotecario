from django.shortcuts import render, redirect, get_object_or_404
from .models import Emprestimo
from .forms import EmprestimoForm

# Create your views here.

def novo_emprestimo(request):
    if request.method == "POST":
        form = EmprestimoForm(request.POST)

        print(form.is_valid())
        print(form.errors)

        if form.is_valid():
            emprestimo = form.save()
            print("salvou karai")
            print("id:", emprestimo.id)

            return redirect("listar_emprestimo")
    else:
        form = EmprestimoForm()

    return render(request, "novo_emprestimo.html", {"form" : form})

def listar_emprestimo(request):
    emprestimos = Emprestimo.objects.all()

    return render(request, "listar_emprestimo.html", {"emprestimos" : emprestimos})

def editar_emprestimo(request, emprestimo_id):
    emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id)

    if request.method == "POST":
        form = EmprestimoForm(request.POST, instance=emprestimo)

        if form.is_valid():
            form.save()
            return redirect("listar_emprestimo")
    else:
        form = EmprestimoForm(instance=emprestimo)
    return render(request, "editar_emprestimo.html", {"form" : form,
                                                      "emprestimo" : emprestimo})


def finalizar_emprestimo(request, emprestimo_id):
    emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id)
    emprestimo.delete()

    return redirect("listar_emprestimo")