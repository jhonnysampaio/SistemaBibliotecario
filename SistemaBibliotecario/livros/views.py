from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Livros, Categoria
from .forms import LivroForm

# Create your views here.

def listar_livro(request):
    livros = Livros.objects.all()

    return render(request, "listar_livro.html",{"livros" : livros})

def cadastrar_livro(request):
    categorias = Categoria.objects.all()

    if request.method == "POST":
        form = LivroForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("listar_livro")

    else:
        
        form = LivroForm()
        print(form.errors)
    return render(request, "cadastrar_livro.html", {"categorias" : categorias,
                                                    "form" : form})

def editar_livro(request, livro_id):
    categorias = Categoria.objects.all()
    livro = get_object_or_404(Livros, id=livro_id)

    if request.method == "POST":
        form = LivroForm(request.POST, instance=livro)

        if form.is_valid():
            form.save()

            return redirect("listar_livro")

    else:
        form = LivroForm(instance=livro)

    return render(request, "editar_livro.html", {"form" : form, 
                                                 "livro" : livro,
                                                 "categorias" : categorias})

def excluir_livro(request, livro_id):
    livro = get_object_or_404(Livros, id=livro_id)
    livro.delete()

    return redirect("listar_livro")
# def val_cad_livro(request):
#     ibsn = request.POST.get("isbn")
#     titulo = request.POST.get("titulo")
#     subtitulo = request.POST.get("subtitulo")
#     autor = request.POST.get("autor")
#     ano = request.POST.get("ano")
#     editora = request.POST.get("editora")
#     categoria = request.POST.get("categoria")
#     cdd = request.POST.get("cdd")
#     local_estante = request.POST.get("local_estante")
#     etiqueta = request.POST.get("etiqueta")
#     quant_total = request.POST.get("quant_total")
#     exemp_disponiveis = request.POST.get("exemp_disponiveis")

#     if 