import unicodedata

# Apelidos de cabecalhos aceitos (ja sem acento, minusculos, com "_").
ALIASES = {
    "e_mail": "email",
    "local_na_estante": "local_estante",
    "ano_de_publicacao": "ano_publicacao",
    "quantidade": "quantidade_total",
}


def sem_acentos(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c))


def normalizar_cabecalho(valor):
    texto = sem_acentos("" if valor is None else valor).strip().lower()
    texto = "_".join(texto.replace("-", " ").split())
    return ALIASES.get(texto, texto)


def normalizar_celula(valor):
    """Devolve sempre texto, sem espacos sobrando. Celula vazia vira ""."""
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)  # 123.0 -> "123"
    return " ".join(str(valor).split())


def chave_comparacao(valor):
    """Para comparar rotulos ignorando acento, caixa e espacos."""
    return sem_acentos(valor).strip().lower()