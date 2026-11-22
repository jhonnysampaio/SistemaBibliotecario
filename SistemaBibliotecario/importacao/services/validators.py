from alunos.forms import AlunoForm
from alunos.models import Aluno
from alunos.validators import somente_digitos
from livros.forms import LivroForm
from livros.models import Categoria
from livros.validators import normalizar_isbn
from .normalizacao import chave_comparacao

COLUNAS = {
    "alunos": {
        "obrigatorias": ["matricula", "nome", "serie", "turma", "turno", "cpf"],
        "opcionais": ["telefone", "email"]
    },
    "livros": {
        "obrigatorias": ["isbn", "titulo", "autor", "editora", "categoria",
                         "cdd", "local_estante", "etiqueta", "quantidade_total"],
        "opcionais": ["subtitulo", "ano_publicacao"],
    },
}

# Campos que nao podem se repetir dentro do mesmo arquivo.
CHAVES_UNICAS = {
    "alunos": {"matricula": lambda v: v.strip().upper(), "cpf": somente_digitos},
    "livros": {"isbn": normalizar_isbn, "etiqueta": lambda v: v.strip().lower()},
}

FORMULARIOS = {"alunos": AlunoForm, "livros": LivroForm}

def verificar_cabecalhos(tipo, cabecalhos):
    cfg = COLUNAS[tipo]
    erros = []
    faltando = [c for c in cfg["obrigatorias"] if c not in cabecalhos]

    if faltando:
        erros.append("Colunas obrigatorias ausentes" + ", ".join(faltando) + ".")
    
    aceitas = cfg["obrigatorias"] + cfg["opcionais"]
    desconhecidas = [c for c in cabecalhos if c not in aceitas]

    if desconhecidas:
        erros.append("Colunas não recohecidas: " + ", ".join(desconhecidas) + ".")
    return erros

def _resolver_opcao(valor, opcoes):
    """
    Converte o rotulo visto pelo usuario no valor guardado no banco.
    """
    chave = chave_comparacao(valor)

    for valor_banco, rotulo in opcoes:
        if chave in (chave_comparacao(valor_banco), chave_comparacao(rotulo)):
            return valor_banco
    return valor    # devolve como veio; o formulario apontara o erro

def _preparar_aluno(bruto):
    dados = dict(bruto)
    dados["serie"] = _resolver_opcao(dados.get("serie", ""), Aluno.Serie.choices)
    dados["turma"] = _resolver_opcao(dados.get("turma", ""), Aluno.Turma.choices)
    dados["turno"] = _resolver_opcao(dados.get("turno", ""), Aluno.Turno.choices)
    dados["ativo"] = "on"   # sem isso o BooleanField do formulario vira False
    return dados, []

def _preparar_livro_factory():
    categorias = {
        chave_comparacao(c.nome): c.pk for c in  Categoria.objects.filter(ativa=True)
    }

    def preparar(bruto):
        dados = dict(bruto)
        extras = []
        pk = categorias.get(chave_comparacao(dados.get("categoria", "")))

        if dados.get("categoria") and pk is None:
            extras.append("Categoria: \"%s\" não existe ou está inativa." % dados["categoria"])
            dados["categoria"] = ""
        else:
            dados["categoria"] = pk or ""
        dados["ativo"] = "on"
        return dados, extras
    
    return preparar

def _erros_do_formulario(form):
    erros = []
    for campo, mensagens in form.errors.items():
        rotulo = "Linha" if campo == "__all__" else form.fields[campo].label or campo
        erros.extend("%s: %s" % (rotulo, m) for m in mensagens)
    return erros

def validar_linhas(tipo, planilha):
    formulario = FORMULARIOS[tipo]
    preparar = _preparar_aluno if tipo == "alunos" else _preparar_livro_factory()
    vistos = {campo : {} for campo in CHAVES_UNICAS[tipo]}
    resultado = []

    for linha in planilha.linhas:
        dados, erros = preparar(linha["dados"])
        form = formulario(dados)
        if not form.is_valid():
            erros += _erros_do_formulario(form)

        for campo, normalizar in CHAVES_UNICAS[tipo].items():
            valor = normalizar(linha["dados"].get(campo, ""))
            if not valor:
                continue
            if valor in vistos[campo]:
                erros.append("%s repetido(a) na linha %d." % (campo, vistos[campo][valor]))
            else:
                vistos[campo][valor] = linha["numero"]

        resultado.append({
            "numero": linha["numero"],
            "dados": dados,
            "valida": not erros,
            "erros": erros,
        })
    return resultado