# Sistema Bibliotecário

Sistema de gestão de biblioteca escolar desenvolvido com Django. Inclui
cadastros, circulação, controle de estoque, perfis de acesso, dashboard,
pesquisa global, alertas internos, reservas, notificações automáticas por
e-mail e verificações de integridade.

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
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale a dependência do projeto:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Entre na pasta da aplicação, onde está o `manage.py`:

```powershell
Set-Location .\SistemaBibliotecario
```

Prepare o banco, os grupos e as permissões:

```powershell
python manage.py migrate
python manage.py configurar_permissoes
```

Crie o administrador local quando o comando solicitar os dados:

```powershell
python manage.py createsuperuser
```

Carregue os dados de demonstração e gere os alertas internos iniciais:

```powershell
python manage.py seed
python manage.py sincronizar_alertas
```

Inicie o servidor de desenvolvimento:

```powershell
python manage.py runserver
```

Enquanto o servidor estiver ativo, os e-mails de cadastro, empréstimo,
devolução, reserva e disponibilidade são enviados quando cada operação é
confirmada no banco. Os avisos de prazo e atraso são sincronizados ao iniciar
o servidor e, depois, exatamente na próxima virada do dia. A expiração de uma
reserva também agenda sua própria próxima verificação, sem varredura fixa a
cada 30 minutos.

Para iniciar o servidor sem o agendador interno de e-mails, defina
`DJANGO_EMAIL_AUTOMACAO_NO_SERVIDOR=False` antes de executar o `runserver`.

Abra `http://127.0.0.1:8000/auth/login/` no navegador.

## Verificação final

Antes de começar uma etapa do tutorial, execute:

```powershell
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py migrate --plan
python manage.py verificar_integridade
python manage.py check
python manage.py test
```

## Escopo desta versão

Esta é uma base didática. Autenticação, permissões, regras de empréstimo,
estoque, testes e preparação para produção serão aprimorados gradualmente ao projeto.
