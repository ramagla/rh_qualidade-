from django.db import models

from .models_tabelatecnica import TabelaTecnica


class Calibracao(models.Model):
    LABORATORIO_CHOICES = [
        ("Ceime", "Ceime"),
        ("Instemaq", "Instemaq"),
        ("Microoptica", "Microoptica"),
        ("Trescal", "Trescal"),
        ("Embracal", "Embracal"),
        ("Kratos", "Kratos"),
        ("Tecmetro", "Tecmetro"),
    ]

    codigo = models.ForeignKey(
        TabelaTecnica, on_delete=models.CASCADE, verbose_name="Código do Equipamento"
    )
    laboratorio = models.CharField(
        max_length=100,
        choices=LABORATORIO_CHOICES,  # Define as opções do select
        verbose_name="Laboratório",
    )
    numero_certificado = models.CharField(
        max_length=100, verbose_name="Número do Certificado"
    )
    erro_equipamento = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="Erro do Equipamento (E)"
    )
    incerteza = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="Incerteza (I)"
    )
    data_calibracao = models.DateField(
        verbose_name="Data da Calibração", null=True, blank=True
    )  # Novo campo
    certificado_anexo = models.FileField(
        upload_to="calibracoes/",
        null=True,
        blank=True,
        verbose_name="Certificado de Calibração",
    )  # Novo campo
    l = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="L", editable=False
    )
    status = models.CharField(
        max_length=20,
        choices=[("Aprovado", "Aprovado"), ("Reprovado", "Reprovado")],
        editable=False,
    )

    def save(self, *args, **kwargs):
        # Calcula o valor de 'L'
        self.l = self.erro_equipamento + self.incerteza

        # Verifica exatidão requerida e define status
        exatidao_requerida = self.codigo.exatidao_requerida
        if self.l <= exatidao_requerida:
            self.status = "Aprovado"
        else:
            self.status = "Reprovado"

        # Salva a instância de Calibracao
        super().save(*args, **kwargs)

        # Atualiza a data da última calibração no modelo TabelaTecnica
        if self.status == "Aprovado" and self.data_calibracao:
            tabela_tecnica = self.codigo
            tabela_tecnica.data_ultima_calibracao = self.data_calibracao
            tabela_tecnica.save()

    def __str__(self):
        return f"{self.codigo} - {self.numero_certificado}"
