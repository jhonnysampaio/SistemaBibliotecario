# Sistema Bibliotecário

Aplicação web para gerenciamento de uma biblioteca escolar, desenvolvida com
Python e Django. O sistema centraliza alunos, livros, empréstimos, devoluções,
reservas, usuários, permissões, notificações internas e comunicações por
e-mail.

## Funcionalidades principais

- Autenticação, alteração de senha e perfis de usuário;
- Grupos e permissões para bibliotecários, auxiliares e direção;
- Cadastro, consulta, edição, ativação e desativação de alunos;
- Séries 1ª, 2ª e 3ª e turmas A, B, C e Téc;
- Fechamento do ano letivo, progressão de série e registro do histórico;
- Cadastro de livros, categorias, ISBN, etiquetas e localização no acervo;
- Importação de alunos e livros por planilhas XLSX ou CSV, com prévia e validação antes da gravação;
- Controle das quantidades total e disponível de cada livro;
- Empréstimos, devoluções, renovações, atrasos e histórico;
- Fila de reservas, liberação do próximo aluno e expiração de reservas;
- Dashboard com indicadores e movimentações recentes;
- Pesquisa global, filtros e paginação;
- Notificações internas;
- Caixa de saída e envio automático de e-mails;
- Comandos para dados de demonstração, permissões e integridade do banco;
- Testes automatizados das regras do sistema.

## Tecnologias

- Python 3.12 ou superior;
- Django 6.0.7;
- SQLite na configuração atual (suporte a PostgreSQL ainda não configurado);
- HTML, CSS e JavaScript;
- Django Templates e Django ORM;
- SMTP do Gmail para envio de e-mails.

## Requisitos

Antes de iniciar, instale:

- [Python 3.12 ou superior](https://www.python.org/downloads/);
- Git, caso o projeto seja obtido pelo GitHub;
- Uma conta do Gmail com senha de aplicativo, caso queira testar os e-mails.

O SQLite já acompanha o Python. Não é necessário instalar um servidor de banco
de dados para executar esta versão do projeto.

## Instalação no Windows

Clone o repositório e entre na pasta principal:

```powershell
git clone https://github.com/jhonnysampaio/SistemaBibliotecario.git
Set-Location .\SistemaBibliotecario
```

Crie o ambiente virtual:

```powershell
py -3.12 -m venv .venv
```

Ative o ambiente:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell impedir a ativação, libere scripts apenas para o usuário atual
e tente novamente:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Atualize o `pip` e instale as dependências:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Entre na pasta que contém o `manage.py`:

```powershell
Set-Location .\SistemaBibliotecario
```

## Instalação no Linux ou macOS

```bash
git clone https://github.com/jhonnysampaio/SistemaBibliotecario.git
cd SistemaBibliotecario
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd SistemaBibliotecario
```

Os comandos `manage.py` das próximas seções devem ser executados dentro da
pasta interna `SistemaBibliotecario`, onde o arquivo está localizado.
Os comandos `python manage.py ...` também funcionam no Bash; para configurar
variáveis de ambiente no Linux/macOS, use os exemplos com `export` na seção
**Variáveis de ambiente**.

## Preparação inicial do banco

Crie ou atualize as tabelas:

```powershell
python manage.py migrate
```

Crie os grupos e atribua as permissões do sistema:

```powershell
python manage.py configurar_permissoes
```

Crie o usuário administrador:

```powershell
python manage.py createsuperuser
```

O comando solicitará nome de usuário, e-mail e senha. A senha digitada não é
exibida no terminal.

Opcionalmente, carregue livros, categorias e alunos de demonstração:

```powershell
python manage.py seed
```

O comando `seed` não apaga registros existentes e pode ser executado novamente
sem duplicar os dados que ele próprio criou.

## Configuração do Gmail SMTP

Esta etapa é opcional para abrir o sistema, mas é necessária para que os
e-mails sejam realmente entregues.

1. Ative a verificação em duas etapas na conta Google usada pela biblioteca.
2. Crie uma senha de aplicativo nas configurações de segurança da conta.
3. Guarde essa senha em uma variável de ambiente. Não coloque a senha no
   código, no README ou no GitHub.

Para configurar apenas o terminal atual do PowerShell:

```powershell
$env:DJANGO_EMAIL_HOST_USER = "seu-email@gmail.com"
$env:DJANGO_EMAIL_HOST_PASSWORD = "senha-de-aplicativo-sem-espacos"
$env:DJANGO_DEFAULT_FROM_EMAIL = $env:DJANGO_EMAIL_HOST_USER
```

Essas variáveis deixam de existir quando o terminal é fechado. Para salvá-las
no perfil do usuário do Windows:

```powershell
[Environment]::SetEnvironmentVariable("DJANGO_EMAIL_HOST_USER", "seu-email@gmail.com", "User")
[Environment]::SetEnvironmentVariable("DJANGO_EMAIL_HOST_PASSWORD", "senha-de-aplicativo-sem-espacos", "User")
[Environment]::SetEnvironmentVariable("DJANGO_DEFAULT_FROM_EMAIL", "seu-email@gmail.com", "User")
```

Depois da configuração permanente, feche e abra o terminal para carregar os
novos valores. Ative novamente o ambiente virtual e entre na pasta do
`manage.py`.

O projeto já utiliza como padrão:

- Servidor: `smtp.gmail.com`;
- Porta: `587`;
- TLS: ativado;
- SSL direto: desativado.

Confira a configuração sem revelar a senha:

```powershell
python manage.py shell -c "from django.conf import settings; print('Host:', settings.EMAIL_HOST); print('Porta:', settings.EMAIL_PORT); print('TLS:', settings.EMAIL_USE_TLS); print('Usuario:', settings.EMAIL_HOST_USER); print('Senha configurada:', bool(settings.EMAIL_HOST_PASSWORD)); print('Remetente:', settings.DEFAULT_FROM_EMAIL)"
```

Envie uma mensagem de teste, substituindo o destinatário:

```powershell
python manage.py shell -c "from django.core.mail import send_mail; print(send_mail('Teste SMTP', 'O servidor SMTP esta funcionando.', None, ['destinatario@example.com'], fail_silently=False))"
```

O retorno `1` indica que o servidor SMTP aceitou uma mensagem para envio.

## Variáveis de ambiente

| Variável | Padrão | Finalidade |
|---|---|---|
| `DJANGO_DEBUG` | `True` | Ativa o modo de desenvolvimento. Só o valor `true` (sem diferenciar maiúsculas) ativa o modo; qualquer outro valor o desativa. |
| `DJANGO_SECRET_KEY` | Chave somente para desenvolvimento | Assinatura criptográfica do Django |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Hosts aceitos, separados por vírgula |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Vazio | Origens HTTPS confiáveis, separadas por vírgula |
| `DJANGO_EMAIL_BACKEND` | Backend SMTP do Django | Mecanismo de envio de e-mail |
| `DJANGO_EMAIL_HOST` | `smtp.gmail.com` | Servidor SMTP |
| `DJANGO_EMAIL_PORT` | `587` | Porta SMTP |
| `DJANGO_EMAIL_HOST_USER` | Vazio | Conta remetente |
| `DJANGO_EMAIL_HOST_PASSWORD` | Vazio | Senha de aplicativo |
| `DJANGO_EMAIL_USE_TLS` | `True` | Ativa TLS |
| `DJANGO_EMAIL_USE_SSL` | `False` | Ativa SSL direto |
| `DJANGO_EMAIL_TIMEOUT` | `20` | Tempo limite da conexão em segundos |
| `DJANGO_DEFAULT_FROM_EMAIL` | Usuário SMTP | Remetente exibido |
| `DJANGO_AVISO_PRAZO_EMPRESTIMO_DIAS` | `2` | Antecedência do aviso de prazo |
| `DJANGO_EMAIL_AUTOMACAO_NO_SERVIDOR` | `True` | Ativa as rotinas enquanto o servidor estiver ligado |

Nas demais variáveis booleanas, `1`, `true`, `yes` e `on` ativam a opção;
outros valores a desativam. Para `DJANGO_DEBUG`, use especificamente `true` ou
`false`.

No Linux ou macOS, defina as variáveis no terminal Bash com `export`:

```bash
export DJANGO_EMAIL_HOST_USER="seu-email@gmail.com"
export DJANGO_EMAIL_HOST_PASSWORD="senha-de-aplicativo-sem-espacos"
export DJANGO_DEFAULT_FROM_EMAIL="$DJANGO_EMAIL_HOST_USER"
```

As variáveis do terminal são temporárias. Em produção, configure-as no serviço
que inicia o Django; não grave senhas no README nem no repositório.

## Execução

Inicie o servidor de desenvolvimento:

```powershell
python manage.py runserver
```

Acesse:

- Login: <http://127.0.0.1:8000/auth/login/>;
- Administração do Django: <http://127.0.0.1:8000/admin/>.

Para encerrar o servidor, pressione `Ctrl+C` no terminal em que ele está sendo
executado.

## Importação de planilhas

Em **Alunos**, **Acervo** ou no menu **Importar planilhas**, é possível cadastrar
vários registros de uma vez a partir de uma planilha `.xlsx` ou `.csv`.

1. Baixe o modelo, preencha a aba `dados` e envie o arquivo. Em XLSX, o sistema
   lê a aba ativa; no modelo, `dados` já é a primeira aba ativa. CSV aceita
   delimitadores vírgula, ponto e vírgula ou tabulação, com UTF-8 ou codificação
   antiga do Windows.
2. Confira a prévia. Linhas com erro bloqueiam a confirmação.
3. Confirme a importação. O sistema revalida as linhas e grava os cadastros em
   uma transação; nenhum aluno ou livro é criado antes da confirmação.

Cabeçalhos obrigatórios e opcionais:

| Importação | Obrigatórios | Opcionais |
|---|---|---|
| Alunos | `matricula`, `nome`, `serie`, `turma`, `turno`, `cpf` | `telefone`, `email` |
| Livros | `isbn`, `titulo`, `autor`, `editora`, `categoria`, `cdd`, `local_estante`, `etiqueta`, `quantidade_total` | `subtitulo`, `ano_publicacao` |

Para livros, a categoria precisa existir e estar ativa antes do envio. A prévia
normalizada é guardada temporariamente no banco por até 2 horas; CPF e telefone
não são exibidos na tabela da prévia. Após a importação, as linhas são apagadas.
Quando uma prévia expira, o comando abaixo limpa suas linhas na próxima execução;
ele também limpa linhas antigas, mas mantém os metadados da importação.

A importação exige as permissões `add_aluno` ou `add_livro`. Arquivos podem ter
até 2 MB e 2.000 linhas. Para apagar diariamente os dados temporários de prévias
expiradas, agende `python manage.py limpar_importacoes` no servidor. Execute o
comando no diretório que contém `manage.py`, usando o mesmo ambiente virtual e
configuração de banco do sistema.

Para iniciar sem o agendador interno de e-mails:

```powershell
$env:DJANGO_EMAIL_AUTOMACAO_NO_SERVIDOR = "False"
python manage.py runserver
```

## E-mails automáticos

O sistema registra e processa mensagens para os seguintes acontecimentos:

- Cadastro de aluno;
- Realização de empréstimo;
- Devolução de empréstimo;
- Empréstimo próximo do prazo;
- Empréstimo atrasado;
- Criação de reserva;
- Livro reservado disponível;
- Solicitação de devolução no fechamento do ano letivo.

Enquanto o `runserver` estiver ativo e
`DJANGO_EMAIL_AUTOMACAO_NO_SERVIDOR=True`, as operações imediatas acordam o
processador da caixa de saída. Os avisos dependentes de datas são sincronizados
ao iniciar o servidor e na próxima mudança de dia. A expiração de uma reserva
agenda sua próxima verificação, sem varredura fixa a cada 30 minutos. Esse
agendador interno inicia somente com `runserver`; ele não é iniciado pelo
servidor WSGI/ASGI de produção.

As mensagens também podem ser processadas manualmente:

```powershell
python manage.py gerar_mensagens
python manage.py enviar_mensagens
```

Para limitar a quantidade processada em uma execução:

```powershell
python manage.py enviar_mensagens --limite 10
```

Em produção, não use `runserver` como agendador. Configure um agendador externo
(por exemplo, cron ou Agendador de Tarefas do Windows) para executar
periodicamente `sincronizar_alertas`, `expirar_reservas`, `gerar_mensagens` e
`enviar_mensagens`; execute `limpar_importacoes` pelo menos uma vez ao dia. O
projeto ainda não fornece um processo único de tarefas em segundo plano para
produção. Use o diretório do `manage.py`, o ambiente virtual e as variáveis do
serviço em cada execução.

## Outros comandos administrativos

Atualize atrasos e notificações internas:

```powershell
python manage.py sincronizar_alertas
```

Expire reservas vencidas e avance suas filas:

```powershell
python manage.py expirar_reservas
```

Verifique a integridade do banco e a coerência do estoque:

```powershell
python manage.py verificar_integridade
```

## Verificações e testes

Execute as verificações recomendadas depois da instalação ou de alterações no
código:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py verificar_integridade
python manage.py test
```

Para verificar as configurações destinadas à produção:

```powershell
python manage.py check --deploy
```

O teste de implantação deve ser executado com as variáveis reais de produção.
Avisos sobre `DEBUG`, HTTPS, cookies seguros ou `SECRET_KEY` são esperados
quando o projeto ainda está configurado para desenvolvimento local.

## Estrutura principal

```text
SistemaBibliotecario/
├── manage.py
├── db.sqlite3
├── SistemaBibliotecario/   # configurações e URLs principais
├── alunos/                  # alunos e fechamento do ano letivo
├── livros/                  # acervo e categorias
├── emprestimos/             # circulação, devoluções e renovações
├── reservas/                # fila e disponibilidade de reservas
├── comunicacoes/            # caixa de saída e e-mails
├── importacao/              # importação e prévias temporárias de planilhas
├── notificacoes/            # alertas internos
├── usuarios/                # autenticação, perfis e permissões
├── dashboard/               # indicadores da biblioteca
├── core/                    # pesquisa e comandos administrativos
├── static/                  # CSS e JavaScript de origem
└── templates/               # templates compartilhados
```

Não exclua os arquivos de migração. A pasta `staticfiles` é gerada por
`collectstatic` e não substitui a pasta `static`.

## Preparação para produção

O servidor `runserver` é destinado somente a desenvolvimento. Antes de uma
publicação real, é necessário:

1. Definir `DJANGO_DEBUG=False`;
2. Gerar uma `DJANGO_SECRET_KEY` longa, aleatória e exclusiva;
3. Configurar `DJANGO_ALLOWED_HOSTS`;
4. Configurar `DJANGO_CSRF_TRUSTED_ORIGINS` com URLs HTTPS completas;
5. Utilizar domínio e certificado HTTPS;
6. Executar `python manage.py collectstatic`;
7. Utilizar um servidor WSGI ou ASGI adequado;
8. Configurar backups automáticos do banco;
9. Configurar um agendador externo para as tarefas temporais; o agendador
   interno só inicia com `runserver` e não substitui um worker de produção;
10. Planejar a migração para PostgreSQL se houver mais acessos simultâneos ou
    maior volume. A configuração atual usa SQLite; mudar o banco exige
    configurar o backend e instalar o driver correspondente.

Nunca publique `DJANGO_SECRET_KEY`, senhas de aplicativo, arquivos `.env` ou o
banco de dados local.

## Problemas comuns

### `OperationalError` ao abrir uma página

Normalmente indica que existem migrações pendentes:

```powershell
python manage.py migrate
```

### Usuário autenticado sem acesso às telas

Recrie os grupos e permissões e confira o cargo do usuário:

```powershell
python manage.py configurar_permissoes
```

### E-mails não enviados

Confirme que:

- O aluno possui um e-mail válido;
- A conta Google possui verificação em duas etapas;
- Foi utilizada uma senha de aplicativo, e não a senha comum da conta;
- As variáveis estão disponíveis no mesmo terminal do `runserver`;
- A porta `587` não está bloqueada pela rede;
- O Gmail não rejeitou ou classificou a mensagem como spam;
- `DJANGO_EMAIL_AUTOMACAO_NO_SERVIDOR` não está definido como `False`.

Consulte também as mensagens registradas na caixa de saída pelo painel
administrativo do Django.
