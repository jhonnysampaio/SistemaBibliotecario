import csv
import io
import zipfile
from dataclasses import dataclass, field
from itertools import islice
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from .normalizacao import normalizar_cabecalho, normalizar_celula

TAMANHO_MAXIMO = 2 * 1024 * 1024  # 2 MB
LINHAS_MAXIMAS = 2000
EXTENSOES = {".xlsx", ".csv"}


class ErroLeitura(Exception):
    """Mensagem segura, escrita para ser exibida ao usuario."""


@dataclass
class Planilha:
    cabecalhos: list
    # [{"numero": 2, "dados": {"matricula": "00123", ...}}, ...]
    linhas: list = field(default_factory=list)


def ler_planilha(arquivo):
    extensao = Path(arquivo.name).suffix.lower()
    if extensao not in EXTENSOES:
        raise ErroLeitura("Formato não suportado. Envie um arquivo .xlsx ou .csv.")
    if arquivo.size > TAMANHO_MAXIMO:
        raise ErroLeitura("O arquivo excede o limite de 2 MB.")

    conteudo = arquivo.read()
    if not conteudo.strip():
        raise ErroLeitura("O arquivo está vazio.")

    if extensao == ".xlsx":
        registros = _ler_xlsx(conteudo)
    else:
        registros = _ler_csv(conteudo)
    return _montar(registros)


def _ler_xlsx(conteudo):
    if not conteudo.startswith(b"PK"):  # XLSX e um arquivo zip
        raise ErroLeitura("O arquivo não é um XLSX válido.")
    try:
        livro = load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
        aba = livro.active  # primeira versao: so a aba ativa
        limite = LINHAS_MAXIMAS + 1000  # folga para linhas em branco
        return [list(l) for l in islice(aba.iter_rows(values_only=True), limite)]
    except (InvalidFileException, zipfile.BadZipFile, KeyError, OSError):
        raise ErroLeitura("Não foi possível ler o XLSX. O arquivo pode estar corrompido.")


def _ler_csv(conteudo):
    try:
        texto = conteudo.decode("utf-8-sig")  # remove o BOM do Excel
    except UnicodeDecodeError:
        texto = conteudo.decode("cp1252", errors="replace")  # CSV antigo do Windows
    try:
        delimitador = csv.Sniffer().sniff(texto[:4096], delimiters=";,\t").delimiter
    except csv.Error:
        delimitador = ";"
    return list(csv.reader(io.StringIO(texto, newline=""), delimiter=delimitador))


def _montar(registros):
    if not registros:
        raise ErroLeitura("A planilha está vazia.")
    cabecalhos = [normalizar_cabecalho(c) for c in registros[0]]
    if not any(cabecalhos):
        raise ErroLeitura("A primeira linha deve conter os cabeçalhos das colunas.")
    repetidos = sorted({c for c in cabecalhos if c and cabecalhos.count(c) > 1})
    if repetidos:
        raise ErroLeitura("Cabeçalhos repetidos: " + ", ".join(repetidos) + ".")

    planilha = Planilha(cabecalhos=[c for c in cabecalhos if c])
    for numero, celulas in enumerate(registros[1:], start=2):
        dados = {
            cab: normalizar_celula(cel)
            for cab, cel in zip(cabecalhos, celulas) if cab
        }
        if not any(dados.values()):
            continue  # ignora linha totalmente em branco
        planilha.linhas.append({"numero": numero, "dados": dados})
        if len(planilha.linhas) > LINHAS_MAXIMAS:
            raise ErroLeitura(
                "A planilha excede o limite de %d linhas." % LINHAS_MAXIMAS
            )
    if not planilha.linhas:
        raise ErroLeitura("A planilha tem cabeçalho, mas nenhuma linha de dados.")
    return planilha