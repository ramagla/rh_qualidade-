# Generated by Django 4.2.16 on 2025-07-31 17:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("comercial", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("qualidade_fornecimento", "0099_alter_fornecedorqualificado_data_homologacao"),
        ("tecnico", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="precalculoservicoexterno",
            name="insumo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="tecnico.insumoetapa",
                verbose_name="Insumo (original do roteiro)",
            ),
        ),
        migrations.AddField(
            model_name="precalculoservicoexterno",
            name="precalculo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="servicos",
                to="comercial.precalculo",
            ),
        ),
        migrations.AddField(
            model_name="precalculoservicoexterno",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Atualizado por",
            ),
        ),
        migrations.AddField(
            model_name="precalculoservicoexterno",
            name="usuario",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="precalculomaterial",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Criado por",
            ),
        ),
        migrations.AddField(
            model_name="precalculomaterial",
            name="fornecedor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="qualidade_fornecimento.fornecedorqualificado",
            ),
        ),
        migrations.AddField(
            model_name="precalculomaterial",
            name="precalculo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="materiais",
                to="comercial.precalculo",
            ),
        ),
        migrations.AddField(
            model_name="precalculomaterial",
            name="roteiro",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="tecnico.roteiroproducao",
                verbose_name="Roteiro de Produção",
            ),
        ),
        migrations.AddField(
            model_name="precalculomaterial",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Atualizado por",
            ),
        ),
        migrations.AddField(
            model_name="precalculomaterial",
            name="usuario",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="precalculo",
            name="cotacao",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="precalculos",
                to="comercial.cotacao",
            ),
        ),
        migrations.AddField(
            model_name="precalculo",
            name="criado_por",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="ordemdesenvolvimento",
            name="cliente",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="comercial.cliente",
                verbose_name="Cliente",
            ),
        ),
        migrations.AddField(
            model_name="ordemdesenvolvimento",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Criado por",
            ),
        ),
        migrations.AddField(
            model_name="ordemdesenvolvimento",
            name="item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="comercial.item",
                verbose_name="Item",
            ),
        ),
        migrations.AddField(
            model_name="ordemdesenvolvimento",
            name="precalculo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="comercial.precalculo",
                verbose_name="Pré-Cálculo",
            ),
        ),
        migrations.AddField(
            model_name="ordemdesenvolvimento",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Atualizado por",
            ),
        ),
        migrations.AddField(
            model_name="ordemdesenvolvimento",
            name="usuario_comercial",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="od_comercial",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="ordemdesenvolvimento",
            name="usuario_tecnico",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="od_tecnico",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="maodeobraferramenta",
            name="ferramenta",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="mao_obra",
                to="comercial.ferramenta",
            ),
        ),
        migrations.AddField(
            model_name="itembloco",
            name="bloco",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="itens",
                to="comercial.blocoferramenta",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="cliente",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="itens",
                to="comercial.cliente",
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="ferramenta",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="itens",
                to="comercial.ferramenta",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="indicadorcomercialregistromensal",
            unique_together={("indicador", "ano", "mes", "trimestre")},
        ),
        migrations.AddField(
            model_name="historicocustocentrodecusto",
            name="centro",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="historico_custos",
                to="comercial.centrodecusto",
            ),
        ),
        migrations.AddField(
            model_name="ferramenta",
            name="bloco",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ferramentas",
                to="comercial.blocoferramenta",
            ),
        ),
        migrations.AddField(
            model_name="ferramenta",
            name="proprietario",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ferramentas",
                to="comercial.cliente",
            ),
        ),
        migrations.AddField(
            model_name="desenvolvimento",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Criado por",
            ),
        ),
        migrations.AddField(
            model_name="desenvolvimento",
            name="precalculo",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="desenvolvimento_item",
                to="comercial.precalculo",
            ),
        ),
        migrations.AddField(
            model_name="desenvolvimento",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Atualizado por",
            ),
        ),
        migrations.AddField(
            model_name="desenvolvimento",
            name="usuario",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="cotacaoferramenta",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Criado por",
            ),
        ),
        migrations.AddField(
            model_name="cotacaoferramenta",
            name="ferramenta",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="comercial.ferramenta"
            ),
        ),
        migrations.AddField(
            model_name="cotacaoferramenta",
            name="precalculo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ferramentas_item",
                to="comercial.precalculo",
            ),
        ),
        migrations.AddField(
            model_name="cotacaoferramenta",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Atualizado por",
            ),
        ),
        migrations.AddField(
            model_name="cotacaoferramenta",
            name="usuario",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="cotacao",
            name="cliente",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="comercial.cliente",
                verbose_name="Cliente",
            ),
        ),
        migrations.AddField(
            model_name="cotacao",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Criado por",
            ),
        ),
        migrations.AddField(
            model_name="cotacao",
            name="responsavel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cotacoes",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Responsável",
            ),
        ),
        migrations.AddField(
            model_name="cotacao",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Atualizado por",
            ),
        ),
        migrations.AddField(
            model_name="clientedocumento",
            name="cliente",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="documentos",
                to="comercial.cliente",
            ),
        ),
        migrations.AddField(
            model_name="cliente",
            name="transportadora",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"tipo_cadastro": "Transportadora"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="clientes_atendidos",
                to="comercial.cliente",
                verbose_name="Transportadora",
            ),
        ),
        migrations.AddField(
            model_name="avaliacaotecnica",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_created",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Criado por",
            ),
        ),
        migrations.AddField(
            model_name="avaliacaotecnica",
            name="precalculo",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="avaliacao_tecnica_item",
                to="comercial.precalculo",
            ),
        ),
        migrations.AddField(
            model_name="avaliacaotecnica",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Atualizado por",
            ),
        ),
        migrations.AddField(
            model_name="avaliacaotecnica",
            name="usuario",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="analisecomercial",
            name="item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="comercial.item",
                verbose_name="Selecione o item",
            ),
        ),
        migrations.AddField(
            model_name="analisecomercial",
            name="precalculo",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="analise_comercial_item",
                to="comercial.precalculo",
            ),
        ),
        migrations.AddField(
            model_name="analisecomercial",
            name="roteiro_selecionado",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="tecnico.roteiroproducao",
                verbose_name="Roteiro Selecionado",
            ),
        ),
        migrations.AddField(
            model_name="analisecomercial",
            name="usuario",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
