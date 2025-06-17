from django.db import models
from comercial.models import Cliente  # certifique-se de importar
import uuid

class Ferramenta(models.Model):
    TIPO_CHOICES = [
        ("Nova", "Ferramenta Nova"),
        ("Adpt", "Adaptação"),
        ("Disp", "Dispositivo"),
        ("Outro", "Outros"),
    ]

    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=255)
    vida_util_em_pecas = models.PositiveIntegerField(verbose_name="Vida útil (em peças)")
    desenho_pdf = models.FileField(upload_to="ferramentas/desenhos/", null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    observacoes = models.TextField(blank=True, null=True)
    proprietario = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name="ferramentas")
    token_cotacao = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    cotacao_enviada_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    

    @property
    def valor_total(self):
        total = 0

        for m in self.materiais.all():
            if m.valor_unitario:
                total += m.quantidade * m.valor_unitario

        for s in self.servicos.all():
            if s.valor_unitario:
                total += s.quantidade * s.valor_unitario

        for mo in self.mao_obra.all():
            if mo.valor_hora:
                total += mo.horas * mo.valor_hora

        return total


    @property
    def status_cotacao(self):
        if not self.materiais.exists() or not self.servicos.exists():
            return "Aguardando Cotação"

        materiais_ok = all(m.valor_unitario is not None for m in self.materiais.all())
        servicos_ok = all(s.valor_unitario is not None for s in self.servicos.all())

        if materiais_ok and servicos_ok:
            return "OK"
        return "Aguardando Cotação"


class MaterialFerramenta(models.Model):
    UNIDADE_CHOICES = [
        ("Kg", "Kg"),
        ("Pc", "Peça"),
        ("Un", "Unidade"),
    ]

    ferramenta = models.ForeignKey(Ferramenta, on_delete=models.CASCADE, related_name="materiais")
    nome_material = models.CharField(max_length=100)
    unidade_medida = models.CharField(max_length=2, choices=UNIDADE_CHOICES)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,  # Permite campo vazio nos formulários
        null=True    # Permite valor nulo no banco de dados
    )
    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario


class MaoDeObraFerramenta(models.Model):
    TIPO_MO_CHOICES = [
        ("Ferramentaria", "Ferramentaria"),
        ("Projeto", "Projeto"),
        ("Externa", "MO Externa"),
    ]

    ferramenta = models.ForeignKey(Ferramenta, on_delete=models.CASCADE, related_name="mao_obra")
    tipo = models.CharField(max_length=20, choices=TIPO_MO_CHOICES)
    horas = models.DecimalField(max_digits=10, decimal_places=2)
    valor_hora = models.DecimalField(max_digits=10,blank=True, null=True, decimal_places=2)

    @property
    def valor_total(self):
        return self.horas * self.valor_hora

class ServicoFerramenta(models.Model):
    SERVICO_CHOICES = [
        ("Eletroerosao", "Eletro erosão"),
        ("Rolamento", "Rolamento"),
        ("Rolete", "Rolete"),
        ("Taxa", "Taxa Administrativa"),
        ("Tratamento", "Tratamento térmico"),
    ]

    ferramenta = models.ForeignKey(Ferramenta, on_delete=models.CASCADE, related_name="servicos")
    tipo_servico = models.CharField(max_length=20, choices=SERVICO_CHOICES)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    valor_unitario = models.DecimalField(max_digits=10,blank=True, null=True, decimal_places=2)

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario
