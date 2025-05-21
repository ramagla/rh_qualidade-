from django.db import models

class VeiculoPortaria(models.Model):
    TIPO_CHOICES = [
        ("carro", "Carro"),
        ("moto", "Moto"),
        ("bicicleta", "Bicicleta"),
        ("caminhao", "Caminhão"),
        ("carreta", "Carreta"),
        ("bau", "Baú"),
        ("outros", "Outros"),
    ]

    placa = models.CharField("Placa", max_length=10, unique=True)
    tipo = models.CharField("Tipo de Veículo", max_length=20, choices=TIPO_CHOICES)

    # 🔗 Pessoa vinculada (nova)
    pessoa = models.ForeignKey(
        "PessoaPortaria", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="veiculos_individuais"
    )

    def __str__(self):
        return f"{self.placa.upper()} ({self.get_tipo_display()})"
    
    def save(self, *args, **kwargs):
        if self.placa:
            self.placa = self.placa.upper()
        super().save(*args, **kwargs)

