import re

from django.core.exceptions import ValidationError


def normalizar_isbn(valor):
    return re.sub(r"[^0-9Xx]", "", valor or "").upper()


def validar_isbn(valor):
    isbn = normalizar_isbn(valor)

    if re.fullmatch(r"\d{9}[\dX]", isbn):
        soma = sum(
            (10 - indice) * (10 if caractere == "X" else int(caractere))
            for indice, caractere in enumerate(isbn)
        )
        valido = soma % 11 == 0
    elif len(isbn) == 13 and isbn.isdigit():
        soma = sum(
            int(caractere) * (1 if indice % 2 == 0 else 3)
            for indice, caractere in enumerate(isbn)
        )
        valido = soma % 10 == 0
    else:
        valido = False

    if not valido:
        raise ValidationError("Informe um ISBN-10 ou ISBN-13 válido.")
