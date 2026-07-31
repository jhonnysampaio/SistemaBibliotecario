from django.db import models
from datetime import date

# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(max_length=50)
    descricao = models.TextField()

    def __str__(self):
        return self.nome

class Livros(models.Model):
    """
    ibn
    título
    subtítulo
    autor
    ano
    editora
    categoria
    assunto - não colocar por enquanto
    cdd
    local na estante
    etiqueta
    quant total
    exemplares disponiveis
    """
    isbn = models.CharField(max_length=17)
    titulo = models.CharField(max_length=100)
    subtitulo = models.CharField(max_length=100, blank = True, null = True)
    autor = models.CharField(max_length=100)
    data_cadastro = models.DateField(default = date.today)
    editora = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete = models.DO_NOTHING)
    cdd = models.CharField(max_length=3)
    local_estante = models.CharField(max_length=100)
    etiqueta = models.CharField(max_length=50)
    quant_total = models.CharField(max_length=10)
    exemp_disponiveis = models.CharField(max_length=10)
    
    class Meta:
        verbose_name = "Livro"
    
    def __str__(self):
        return self.titulo

