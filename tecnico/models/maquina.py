from django.db import models
from rh_qualidade.utils import formatar_nome_atividade_com_siglas  # ajuste conforme o caminho real

class ServicoRealizado(models.Model):
    nome = models.CharField("Serviço", max_length=200, unique=True)

    def save(self, *args, **kwargs):
            if self.nome:
                self.nome = formatar_nome_atividade_com_siglas(self.nome)
            super().save(*args, **kwargs)
            
    def __str__(self):
        return self.nome
    
class Maquina(models.Model):
    FAMILIA_PRODUTO_LABELS = {
        "MCGC": "Mola de Compressão Grupo C",
        "MCGD": "Mola de Compressão Grupo D",
        "MTRAGC": "Mola de Tração Grupo C",
        "MTRAGX": "Mola de Tração Grupo X",
        "MTRAGD": "Mola de Tração Grupo D",
        "MTORGC": "Mola de Torção Grupo C",
        "MTORGX": "Mola de Torção Grupo X",
        "MTORGD": "Mola de Torção Grupo D",
        "PEGE": "Peças Estampadas Grupo E",
        "PEGP": "Peças Estampadas Grupo P",
        "HGD": "Hastes Grupo D",
        "HGM": "Hastes Grupo M",
        "HGE": "Hastes Grupo E",
        "HGC": "Hastes Grupo C",
        "AGC": "Anel Grupo C",
        "AGD": "Anel Grupo D",
        "AGE": "Anel Grupo E",
        "PGC": "Pino Grupo C",
        "PGE": "Pino Grupo E",
    }
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    grupo_de_maquinas = models.CharField(
        max_length=6,
        choices=[(k, v) for k, v in FAMILIA_PRODUTO_LABELS.items()],
        verbose_name="Grupo de Máquinas"
    )
    servicos_realizados = models.ManyToManyField(ServicoRealizado, blank=True, verbose_name="Serviços Realizados")
    velocidade = models.DecimalField(max_digits=10, decimal_places=2, help_text="Unidade do produto por hora")
    valor_hora = models.DecimalField(max_digits=10, decimal_places=2)
    consumo_kwh = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
            if self.codigo:
                self.codigo = self.codigo.upper()

            if self.nome:
                self.nome = formatar_nome_atividade_com_siglas(self.nome)

            super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    

