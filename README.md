# Sistema Bibliotecário

Versão inicial de um sistema de biblioteca escolar desenvolvido com Django.
Este repositório é o ponto de partida do tutorial de evolução do projeto.

## Requisitos

- Python 3.12 ou superior
- Git

## Instalação no Windows

Clone o repositório e entre na pasta criada:

```powershell
git clone https://github.com/jhonnysampaio/SistemaBibliotecario.git
cd SistemaBibliotecario
```

Crie e ative um ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale a dependência do projeto:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Prepare o banco de dados local:

```powershell
python SistemaBibliotecario\manage.py migrate
```

Inicie o servidor de desenvolvimento:

```powershell
python SistemaBibliotecario\manage.py runserver
```

Abra `http://127.0.0.1:8000/auth/login/` no navegador.

## Verificação rápida

Antes de começar uma etapa do tutorial, execute:

```powershell
python SistemaBibliotecario\manage.py check
python SistemaBibliotecario\manage.py makemigrations --check --dry-run
```

O banco `db.sqlite3`, o ambiente virtual e os caches do Python são arquivos
locais e não devem ser enviados ao Git.

## Escopo desta versão

Esta é uma base didática. Autenticação, permissões, regras de empréstimo,
estoque, testes e preparação para produção serão aprimorados gradualmente no
tutorial.
