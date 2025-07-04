from django.db import models
from comercial.models import Cliente
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator

class BlocoFerramenta(models.Model):
    numero = models.CharField("Bloco", max_length=50)

    @property
    def peso_total(self) -> Decimal:
        # soma peso_total de cada item; use Decimal para evitar float impreciso
        return sum(Decimal(str(item.peso_total or 0)) for item in self.itens.all())


    def __str__(self):
        return self.numero

    
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

    # campos a adicionar em Ferramenta
    peso_sae_kg = models.DecimalField("Peso SAE 1020 (Kg)", max_digits=10, decimal_places=3, null=True, blank=True)
    valor_unitario_sae = models.DecimalField("Valor Unitário SAE 1020 (R$/Kg)", max_digits=10, decimal_places=2, null=True, blank=True)

    peso_vnd_kg = models.DecimalField("Peso VND (Kg)", max_digits=10, decimal_places=3, null=True, blank=True)
    valor_unitario_vnd = models.DecimalField("Valor Unitário VND (R$/Kg)", max_digits=10, decimal_places=2, null=True, blank=True)



    def __str__(self):
        return f"{self.codigo} - {self.descricao}" if self.codigo else "Ferramenta sem código"

    # Cálculo automático de materiais (em Kg)
    @property
    def kg_matriz(self):
        if self.largura_tira and self.passo and self.num_matrizes:
            return (
                (self.largura_tira + Decimal("20")) *
                (self.passo + Decimal("20")) *
                Decimal("19") *
                Decimal("7.86") *
                self.num_matrizes
            ) / Decimal("1000000")
        return None

    @property
    def kg_puncao(self):
        if self.largura_tira and self.passo and self.num_puncoes:
            return (
                (self.largura_tira + Decimal("5")) *
                (self.passo + Decimal("5")) *
                Decimal("50") *
                Decimal("7.86") *
                self.num_puncoes
            ) / Decimal("1000000")
        return None


    @property
    def kg_flange(self):
        if self.largura_tira:
            return (
                Decimal("200") *
                Decimal("200") *
                (Decimal("33") + self.largura_tira) *
                Decimal("7.86")
            ) / Decimal("1000000")
        return None


    @property
    def kg_carros(self):
        if self.num_carros:
            return Decimal("2.5") * self.num_carros
        return None




    @property
    def kg_formadores(self):
        if self.largura_tira and self.num_formadores:
            return (
                self.largura_tira *
                self.num_formadores *
                Decimal("25") *
                Decimal("150")
            ) / Decimal("1000000")
        return None


    from decimal import Decimal

    @property
    def valor_total(self):
        total = Decimal(0)

        # Materiais
        if self.valor_unitario_sae and (self.peso_sae_kg or self.kg_carros):
            total += self.valor_unitario_sae * ((self.peso_sae_kg or 0) + (self.kg_carros or 0))

        if self.valor_unitario_vnd and self.peso_vnd_kg:
            total += self.valor_unitario_vnd * self.peso_vnd_kg

        if self.valor_unitario_matriz and self.kg_matriz:
            total += self.valor_unitario_matriz * self.kg_matriz

        if self.valor_unitario_puncao and self.kg_puncao:
            total += self.valor_unitario_puncao * self.kg_puncao

        if self.valor_unitario_formadores and self.kg_formadores:
            total += self.valor_unitario_formadores * self.kg_formadores

        if self.valor_unitario_flange and self.kg_flange:
            total += self.valor_unitario_flange * self.kg_flange

        # Serviços
        for s in self.servicos.all():
            if s.valor_unitario is not None:
                total += s.quantidade * s.valor_unitario

        # Mão de obra
        for mo in self.mao_obra.all():
            if mo.valor_hora:
                total += mo.horas * mo.valor_hora

        return total



    @property
    def status_cotacao(self):
        servicos_ok = all(s.valor_unitario is not None for s in self.servicos.all())
        materiais_ok = (self.valor_unitario_carros or 0) > 0 or (self.valor_unitario_formadores or 0) > 0

        if not self.servicos.exists() and not materiais_ok:
            return "Aguardando Cotação"

        if not servicos_ok or not materiais_ok:
            return "Aguardando Cotação"

        return "OK"
    
    @property
    def pode_enviar_cotacao(self):
        materiais = [
            self.valor_unitario_matriz,
            self.valor_unitario_puncao,
            self.valor_unitario_flange,
            self.valor_unitario_carros,
            self.valor_unitario_formadores,
            self.valor_unitario_sae,
            self.valor_unitario_vnd,
        ]

        if any(v is None for v in materiais):
            return True

        if self.servicos.filter(valor_unitario__isnull=True).exists():
            return True

        return False











class ItemBloco(models.Model):
    bloco = models.ForeignKey(BlocoFerramenta, on_delete=models.CASCADE, related_name="itens")
    numero_item = models.CharField("Nº Item", max_length=20)
    medidas = models.CharField("Medidas (ex: 25,4x94x165)", max_length=100)
    material = models.CharField("Material", max_length=50, choices=[("SAE 1020", "SAE 1020"), ("VND", "VND")])
    peso_aco = models.DecimalField("Peso Aço", max_digits=5, decimal_places=2, default=7.86)

    volume = models.DecimalField("Volume", max_digits=10, decimal_places=2, null=True, blank=True)
    peso_total = models.DecimalField("Peso Total", max_digits=10, decimal_places=2, null=True, blank=True)

    def calcular_volume_e_peso(self):
        try:
            comp, larg, alt = [float(m.replace(",", ".")) for m in self.medidas.lower().split("x")]
            volume = (comp * larg * alt) / 1000000  # mm³ → cm³ → Kg (1.000.000 mm³ = 1 L)
            peso = volume * float(self.peso_aco)  # Peso = volume * densidade (7.86)

            self.volume = round(volume, 2)
            self.peso_total = round(peso, 2)
        except Exception:
            self.volume = None
            self.peso_total = None

    def save(self, *args, **kwargs):
        self.calcular_volume_e_peso()
        super().save(*args, **kwargs)

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
