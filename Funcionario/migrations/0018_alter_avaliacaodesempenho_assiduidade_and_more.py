# Generated by Django 5.1.2 on 2024-10-25 16:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0017_avaliacaodesempenho_adaptacao_trabalho_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="assiduidade",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="comprometimento",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="comunicacao",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="disciplina",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="disponibilidade_para_mudancas",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="postura_seg_trabalho",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="proatividade",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="qualidade_produtividade",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="rendimento_sob_pressao",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="avaliacaodesempenho",
            name="trabalho_em_equipe",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="AvaliacaoAnual",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data_avaliacao", models.DateField()),
                (
                    "centro_custo",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("gerencia", models.CharField(blank=True, max_length=100, null=True)),
                ("postura_seg_trabalho", models.IntegerField()),
                ("qualidade_produtividade", models.IntegerField()),
                ("trabalho_em_equipe", models.IntegerField()),
                ("comprometimento", models.IntegerField()),
                ("disponibilidade_para_mudancas", models.IntegerField()),
                ("disciplina", models.IntegerField()),
                ("rendimento_sob_pressao", models.IntegerField()),
                ("proatividade", models.IntegerField()),
                ("comunicacao", models.IntegerField()),
                ("assiduidade", models.IntegerField()),
                ("observacoes", models.TextField(blank=True, null=True)),
                (
                    "avaliado",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="avaliado_anual",
                        to="Funcionario.funcionario",
                    ),
                ),
                (
                    "avaliador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="avaliador_anual",
                        to="Funcionario.funcionario",
                    ),
                ),
                (
                    "funcionario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="Funcionario.funcionario",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AvaliacaoExperiencia",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data_avaliacao", models.DateField()),
                ("gerencia", models.CharField(blank=True, max_length=100, null=True)),
                ("adaptacao_trabalho", models.IntegerField(blank=True, null=True)),
                ("interesse", models.IntegerField(blank=True, null=True)),
                ("relacionamento_social", models.IntegerField(blank=True, null=True)),
                ("capacidade_aprendizagem", models.IntegerField(blank=True, null=True)),
                ("observacoes", models.TextField(blank=True, null=True)),
                (
                    "funcionario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="Funcionario.funcionario",
                    ),
                ),
            ],
        ),
    ]
