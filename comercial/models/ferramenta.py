from django.db import models
from comercial.models import Cliente
import uuid

class BlocoFerramenta(models.Model):
    numero = models.CharField("Bloco", max_length=50)

    def __str__(self):
        return f"Bloco {self.numero}"
    
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

    # Campos para cálculo de materiais
    passo = models.DecimalField("Passo", max_digits=10, decimal_places=2, null=True, blank=True)
    largura_tira = models.DecimalField("Largura da Tira / Perímetro de Corte", max_digits=10, decimal_places=2, null=True, blank=True)
    num_matrizes = models.PositiveIntegerField("Número de Matrizes", null=True, blank=True)
    num_puncoes = models.PositiveIntegerField("Número de Punções", null=True, blank=True)
    num_carros = models.PositiveIntegerField("Número de Carros", null=True, blank=True)
    num_formadores = models.PositiveIntegerField("Número de Formadores", null=True, blank=True)
    bloco = models.ForeignKey(
        BlocoFerramenta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ferramentas"
    )

    # Valores de cotação por kg (preenchidos manualmente)
    valor_unitario_matriz = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_unitario_puncao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_unitario_flange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_unitario_carros = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_unitario_formadores = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

    # Cálculo automático de materiais (em Kg)
    @property
    def kg_matriz(self):
        if self.largura_tira and self.passo and self.num_matrizes:
            return ((self.largura_tira + 20) * (self.passo + 20) * 19 * 7.86 * self.num_matrizes) / 1_000_000
        return None

    @property
    def kg_puncao(self):
        if self.largura_tira and self.passo and self.num_puncoes:
            return ((self.largura_tira + 5) * (self.passo + 5) * 50 * 7.86 * self.num_puncoes) / 1_000_000
        return None

    @property
    def kg_flange(self):
        if self.largura_tira:
            return (200 * 200 * (33 + self.largura_tira) * 7.86) / 1_000_000
        return None

    @property
    def kg_carros(self):
        if self.num_carros:
            return 2.5 * self.num_carros
        return None

    @property
    def kg_formadores(self):
        if self.largura_tira and self.num_formadores:
            return (self.largura_tira * self.num_formadores * 25 * 150) / 1_000_000
        return None

    @property
    def valor_total(self):
        total = 0
        for s in self.servicos.all():
            if s.valor_unitario:
                total += s.quantidade * s.valor_unitario
        for mo in self.mao_obra.all():
            if mo.valor_hora:
                total += mo.horas * mo.valor_hora
        return total

    @property
    def status_cotacao(self):
        servicos_ok = all(s.valor_unitario is not None for s in self.servicos.all())
        if not self.servicos.exists():
            return "Aguardando Cotação"
        return "OK" if servicos_ok else "Aguardando Cotação"





class ItemBloco(models.Model):
    bloco = models.ForeignKey(BlocoFerramenta, on_delete=models.CASCADE, related_name="itens")
    numero_item = models.CharField("Nº Item", max_length=20)
    medidas = models.CharField("Medidas (ex: 25,4x94x165)", max_length=100)
    material = models.CharField("Material", max_length=50, choices=[("SAE 1020", "SAE 1020"), ("VND", "VND")])
    peso_aco = models.DecimalField("Peso Aço", max_digits=5, decimal_places=2, default=7.86)

    @property
    def volume(self):
        try:
            comp, larg, alt = [float(m.replace(",", ".")) for m in self.medidas.lower().split("x")]
            return comp * larg * alt
        except Exception:
            return 0

    @property
    def peso_total(self):
        return (self.volume * self.peso_aco) / 1_000_000

    def __str__(self):
        return f"{self.numero_item} - {self.material}"


class MaoDeObraFerramenta(models.Model):
    TIPO_MO_CHOICES = [
        ("Ferramentaria", "Ferramentaria"),
        ("Projeto", "Projeto"),
        ("Externa", "MO Externa"),
    ]

    ferramenta = models.ForeignKey(Ferramenta, on_delete=models.CASCADE, related_name="mao_obra")
    tipo = models.CharField(max_length=20, choices=TIPO_MO_CHOICES)
    horas = models.DecimalField(max_digits=10, decimal_places=2)
    valor_hora = models.DecimalField(max_digits=10, blank=True, null=True, decimal_places=2)

    @property
    def valor_total(self):
        return self.horas * self.valor_hora if self.valor_hora else 0

    def __str__(self):
        return f"{self.ferramenta.codigo} - {self.tipo}"


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
    valor_unitario = models.DecimalField(max_digits=10, blank=True, null=True, decimal_places=2)

    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario if self.valor_unitario else 0

    def __str__(self):
        return f"{self.ferramenta.codigo} - {self.tipo_servico}"
