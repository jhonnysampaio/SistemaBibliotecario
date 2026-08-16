import re
from django.core.exceptions import ValidationError

def somente_digitos(valor):
    return re.sub(r"\D", "", valor or "")

def validar_cpf(valor):
    cpf = somente_digitos(valor)

    if len(cpf) != 11 or cpf == cpf[0] *11:
        raise ValidationError("Informe um CPF válido.")

    for tamanho in(9, 10):
        soma = sum(
            int(cpf[indice]) * (tamanho + 1 - indice)
            for indice in range(tamanho)
        )
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[tamanho]):
            raise ValidationError("Informe um CPF válido.")