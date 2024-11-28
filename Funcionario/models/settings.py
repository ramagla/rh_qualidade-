from django.db import models

class Settings(models.Model):
    nome_empresa = models.CharField(max_length=100, default="BRAS-MOL MOLAS & ESTAMPADOS LTDA")
    cep = models.CharField(max_length=20, default="08579000")
    endereco = models.CharField(max_length=150, default="BONSUCESSO, DO, 1961 - RIO ABAIXO - Itaquaquecetuba / SP")
    telefone = models.CharField(max_length=20, default="1146482611")
    email = models.EmailField(default="rh@brasmol.com.br")
    cnpj = models.CharField(max_length=20, default="61.296.901/0002-48")
    
    logo_claro = models.ImageField(upload_to='logos/', null=True, blank=True)
    logo_escuro = models.ImageField(upload_to='logos/', null=True, blank=True)

    class Meta:
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"

    def save(self, *args, **kwargs):
        if not Settings.objects.filter(pk=self.pk).exists() and Settings.objects.exists():
            self.pk = Settings.objects.first().pk
        super(Settings, self).save(*args, **kwargs)

    def __str__(self):
        return self.nome_empresa
