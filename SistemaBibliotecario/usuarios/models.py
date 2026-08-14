from django.conf import settings
from django.db import models

# Create your models here.

class Perfil(models.Model):
    class Cargo(models.TextChoices):
        BIBLIOTECARIO = "BIB", "Bibliotecário" 
        AUXILIAR = "AUX", "Auxiliar"
        DIRECAO = "DIR", "Direção"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="perfil",         
    )
    cargo = models.CharField(
        max_length=3,
        choices=Cargo.choices,
        default=Cargo.AUXILIAR,
    )
    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfis"

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.get_cargo_display()}"
