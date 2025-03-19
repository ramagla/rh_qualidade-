from django.db import models
from django.utils.timezone import now

from Funcionario.models import Funcionario
from metrologia.models.models_tabelatecnica import TabelaTecnica


class Dispositivo(models.Model):
    UNIDADE_MEDIDA_CHOICES = [
        ("mm", "Milímetros"),
        ("cm", "Centímetros"),
        ("m", "Metros"),
        ("kg", "Quilogramas"),
        ("°C", "Graus Celsius"),
        ("%", "Percentual"),
        ("Ø", "Diâmetro"),
    ]

    ESTUDO_REALIZADO_CHOICES = [
        ("POR ATRIBUTO (MÉTODO CURTO)", "Por Atributo (Método Curto)"),
        ("NÃO PASSA", "Não Passa"),
        ("CALIBRAÇÃO PELO CLIENTE", "Calibração é realizada pelo cliente"),
    ]

    codigo = models.CharField(
        max_length=50, unique=True, verbose_name="Código do Dispositivo"
    )
    qtde = models.PositiveIntegerField(verbose_name="Quantidade")
    cliente = models.CharField(max_length=100, verbose_name="Cliente")
    descricao = models.CharField(
        max_length=255, verbose_name="Descrição"
    )  # Texto curto
    estudo_realizado = models.CharField(
        max_length=50, choices=ESTUDO_REALIZADO_CHOICES, verbose_name="Estudo Realizado"
    )
    data_ultima_calibracao = models.DateField(
        null=True, blank=True, verbose_name="Data da Última Calibração"
    )
    frequencia_calibracao = models.PositiveIntegerField(
        verbose_name="Frequência de Calibração (em meses)"
    )
    local_armazenagem = models.CharField(
        max_length=100, verbose_name="Local de Armazenagem"
    )

    unidade_medida = models.CharField(
        max_length=10, choices=UNIDADE_MEDIDA_CHOICES, verbose_name="Unidade de Medida"
    )
    desenho_anexo = models.FileField(
        upload_to="dispositivos/desenhos/",
        null=True,
        blank=True,
        verbose_name="Desenho do Dispositivo",
    )
    updated_at = models.DateTimeField(auto_now=True)
    alteracao = models.TextField(blank=True, null=True, verbose_name="Última Alteração")

    def save(self, *args, **kwargs):
        alteracoes = []
        if self.pk:  # Se o registro já existir
            original = Dispositivo.objects.get(pk=self.pk)

            # Verificar alterações campo por campo
            campos_para_verificar = [
                "descricao",
                "cliente",
                "local_armazenagem",
                "frequencia_calibracao",
                "qtde",
                "estudo_realizado",
                "data_ultima_calibracao",
                "unidade_medida",
                "desenho_anexo",
            ]
            for campo in campos_para_verificar:
                valor_original = getattr(original, campo)
                valor_atual = getattr(self, campo)
                if valor_original != valor_atual:
                    alteracoes.append(
                        f"{campo.replace('_', ' ').capitalize()} alterado de '{valor_original}' para '{valor_atual}'"
                    )

        # Atualizar campo de alteração
        if alteracoes:
            self.alteracao = "; ".join(alteracoes)

        # Formatações específicas
        if self.codigo:
            self.codigo = self.codigo.upper()
        if self.local_armazenagem:
            self.local_armazenagem = self.local_armazenagem.upper()
        if self.cliente:
            self.cliente = self.cliente.title()
        if self.descricao:
            self.descricao = self.descricao.title()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo


class Cota(models.Model):
    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.CASCADE,
        related_name="cotas",
        verbose_name="Dispositivo",
    )
    numero = models.PositiveIntegerField(verbose_name="Número da Cota")
    valor_minimo = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="Valor Mínimo"
    )
    valor_maximo = models.DecimalField(
        max_digits=10, decimal_places=3, verbose_name="Valor Máximo"
    )

    def __str__(self):
        return f"Cota {self.numero} do Dispositivo {self.dispositivo.codigo}"


class ControleEntradaSaida(models.Model):
    SITUACAO_CHOICES = [
        ("OK", "Ok"),
        ("NOK", "Nok"),
    ]

    TIPO_MOVIMENTACAO_CHOICES = [
        ("entrada", "Entrada"),
        ("saida", "Saída"),
    ]

    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.CASCADE,
        related_name="controle_entrada_saida",
        verbose_name="Código do Dispositivo",
    )
    tipo_movimentacao = models.CharField(
        max_length=10,
        choices=TIPO_MOVIMENTACAO_CHOICES,
        verbose_name="Tipo de Movimentação",
    )
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade", default=1)
    data_movimentacao = models.DateField(
        verbose_name="Data da Movimentação", null=True, blank=True
    )
    colaborador = models.ForeignKey(
        Funcionario, on_delete=models.CASCADE, verbose_name="Colaborador"
    )
    setor = models.CharField(
        max_length=100, verbose_name="Setor", blank=True, null=True
    )
    situacao = models.CharField(
        max_length=3, choices=SITUACAO_CHOICES, verbose_name="Situação"
    )
    observacao = models.TextField(null=True, blank=True, verbose_name="Observação")

    def __str__(self):
        return f"Dispositivo {self.dispositivo.codigo} - {self.situacao} ({self.get_tipo_movimentacao_display()})"
