from django.db import models


class Settings(models.Model):
    """
    Configurações gerais do sistema, contendo informações da empresa e logotipos utilizados na interface.
    Deve existir apenas uma instância dessa classe (singleton).
    """

    nome_empresa = models.CharField(
        max_length=100,
        default="BRAS-MOL MOLAS & ESTAMPADOS LTDA",
        verbose_name="Nome da Empresa"
    )
    cep = models.CharField(
        max_length=20,
        default="08579000",
        verbose_name="CEP"
    )
    endereco = models.CharField(
        max_length=150,
        default="BONSUCESSO, DO, 1961 - RIO ABAIXO - Itaquaquecetuba / SP",
        verbose_name="Endereço"
    )
    telefone = models.CharField(
        max_length=20,
        default="1146482611",
        verbose_name="Telefone"
    )
    email = models.EmailField(
        default="rh@brasmol.com.br",
        verbose_name="E-mail"
    )
    cnpj = models.CharField(
        max_length=20,
        default="61.296.901/0002-48",
        verbose_name="CNPJ"
    )

    logo_claro = models.ImageField(
        upload_to="logos/",
        null=True,
        blank=True,
        verbose_name="Logo (Claro)"
    )
    logo_escuro = models.ImageField(
        upload_to="logos/",
        null=True,
        blank=True,
        verbose_name="Logo (Escuro)"
    )

    class Meta:
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que exista apenas uma única instância deste modelo.
        """
        if (
            not Settings.objects.filter(pk=self.pk).exists()
            and Settings.objects.exists()
        ):
            self.pk = Settings.objects.first().pk
        super(Settings, self).save(*args, **kwargs)

    def __str__(self):
        return self.nome_empresa
