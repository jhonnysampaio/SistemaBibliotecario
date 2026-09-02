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

O resultado esperado é: migrações aplicadas, nenhum plano pendente,
integridade confirmada, nenhuma nova migração detectada e testes aprovados.

## Rotina operacional

Execute periodicamente os comandos abaixo (por exemplo, pelo Agendador de
Tarefas do Windows) para atualizar alertas, criar mensagens sem duplicá-las e
enviar a caixa de saída:

```powershell
python manage.py sincronizar_alertas
python manage.py expirar_reservas
python manage.py gerar_mensagens
python manage.py enviar_mensagens --limite 50
```

O sistema gera e-mails para cadastro de aluno, realização de empréstimo,
proximidade do prazo de devolução, atraso e disponibilidade de reserva. Por
padrão, o lembrete de prazo é criado quando faltam até dois dias. Esse período
pode ser alterado pela variável `DJANGO_AVISO_PRAZO_EMPRESTIMO_DIAS`.

As credenciais SMTP devem ser fornecidas pelas variáveis de ambiente
`DJANGO_EMAIL_HOST_USER`, `DJANGO_EMAIL_HOST_PASSWORD` e demais configurações
`DJANGO_EMAIL_*`. Nunca grave a senha de aplicativo no código ou no Git.

O banco `db.sqlite3`, o ambiente virtual e os caches do Python são arquivos
locais e não devem ser enviados ao Git.

Para uma publicação real, defina `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`,
`DJANGO_ALLOWED_HOSTS` e, quando houver HTTPS, as origens confiáveis de CSRF.
Não reutilize credenciais ou o banco de demonstração em produção.
