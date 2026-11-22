import io
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from openpyxl import Workbook
from .forms import ArquivoPlanilhaForm
from .models import ImportacaoPlanilha
from .services.importador import (ImportacaoNaoPermitida, LinhaRejeitada,
 confirmar_importacao, criar_previa)
from .services.leitor import LINHAS_MAXIMAS, TAMANHO_MAXIMO, ErroLeitura
from .services.validators import COLUNAS

# Create your views here.
TIPOS = {
    
    "alunos": {"titulo": "alunos", "permissao": "alunos.add_aluno",
               "retorno": "alunos:lista", "texto": ["matricula", "cpf", "telefone"]},    
    "livros": {"titulo": "livros", "permissao": "livros.add_livro",
               "retorno": "livros:lista", "texto": ["isbn", "etiqueta", "cdd"]},
}

def _config(requet, tipo):
    config = TIPOS.get(tipo)

    if config is None:
       raise Http404
    if not requet.user.has_perm(config["permissao"]):
        raise PermissionDenied

    return config

def _resumo(tipo, dados):
    # Nao ha exibicao do CPF e nem do telefone na prévia: apenas o necessario para identificar cada linha.
    if tipo == "alunos":
        return "%s - %s" % (dados.get("matricula", ""), dados.get("nome", ""))
    return "%s - %s" % (dados.get("isbn", ""), dados.get("titulo", ""))

@login_required
def inicio(request):
    permitidos = {t: c for t, c in TIPOS.items() if request.user.has_perm(c["permissao"])}

    if not permitidos:
        raise PermissionDenied
    return render(request, "importacao/inicio.html", {"tipos": permitidos})

@login_required
def modelo(request, tipo):
    config = _config(request, tipo)
    cabecalhos = COLUNAS[tipo]["obrigatorias"] + COLUNAS[tipo]["opcionais"]

    wb = Workbook()
    ws = wb.active
    ws.title = "dados"
    ws.append(cabecalhos)

    for indice, nome in enumerate(cabecalhos, start=1):
        if nome in config["texto"]:    # formato Texto preserva zeros a esquerda
            for linha in range(2, 1002):
                ws.cell(row=linha, column=indice).number_format = "@"

    ajuda = wb.create_sheet("instrucoes")
    ajuda.append(["Preencha a aba 'dados', uma linha por registro."])
    ajuda.append(["Nao altere os cabecalhos. Nao use formulas: cole apenas valores."])
    ajuda.append(["Matricula, CPF, ISBN e etiqueta devem permanecer como texto."])
    ajuda.append(["Limite: %d linhas e %d MB." % (LINHAS_MAXIMAS, TAMANHO_MAXIMO // 1048576)])

    buffer = io.BytesIO()
    wb.save(buffer)
    resposta = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    resposta["Content-Disposition"] = 'attachment; filename="modelo_%s.xlsx"' % tipo
    return resposta

@login_required
def enviar(request, tipo):
    config = _config(request, tipo)
    form = ArquivoPlanilhaForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            importacao = criar_previa(
                usuario=request.user, tipo=tipo, arquivo=form.cleaned_data["arquivo"]
            )
        except ErroLeitura as erro:
            form.add_error("arquivo", str(erro))
        else:
            return redirect("importacao:previa", pk=importacao.pk)
    return render(request, "importacao/enviar.html", {
        "form": form, "tipo": tipo, "config": config, "colunas": COLUNAS[tipo],
        "limite_linhas": LINHAS_MAXIMAS, "limite_mb": TAMANHO_MAXIMO // 1048576
    })

@login_required
def previa(request, pk):
    importacao = get_object_or_404(ImportacaoPlanilha, pk=pk, usuario=request.user)
    config = _config(request, importacao.tipo)
    linhas = [
        {"numero": l["numero"], "resumo": _resumo(importacao.tipo, l["dados"]),
         "valida": l["valida"], "erros": l["erros"]}
         for l in importacao.linhas
    ]
    invalidas = [l for l in linhas if not l["valida"]]
    validas = [l for l in linhas if l["valida"]][:50] # amostra

    return render(request, "importacao/previa.html", {
        "importacao": importacao, "config": config,
        "invalidas": invalidas, "validas": validas,
        "pode_confirmar": (
            importacao.status == ImportacaoPlanilha.Status.VALIDADA
            and not importacao.expirada and importacao.total_invalidas == 0
        ),
    })

@login_required
@require_POST
def confirmar(request, pk):
    importacao = get_object_or_404(ImportacaoPlanilha, pk=pk, usuario=request.user)
    config = _config(request, importacao.tipo)
    try:
        concluida = confirmar_importacao(importacao_id=pk, usuario=request.user)
    except ImportacaoNaoPermitida as erro:
        messages.error(request, str(erro))
        return redirect("importacao:previa", pk=pk)
    except LinhaRejeitada as erro:
        ImportacaoPlanilha.objects.filter(
            pk=pk, status=ImportacaoPlanilha.Status.VALIDADA
        ).update(status=ImportacaoPlanilha.Status.FALHOU)
        onde = "Linha %s: " % erro.numero if erro.numero else ""
        messages.error(request, "Nada foi importado. %s%s" % (onde, "; ".join(erro.erros)))
        return redirect("importacao:previa", pk=pk)
    
    messages.success(
        request, "%d registro(s) importado(s)." % concluida.total_importadas
    )
    return redirect(config["retorno"])