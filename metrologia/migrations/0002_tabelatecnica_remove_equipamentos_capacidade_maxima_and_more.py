# Generated by Django 5.1.2 on 2024-12-10 12:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0089_alter_funcionario_formulario_f146"),
        ("metrologia", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TabelaTecnica",
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
                (
                    "codigo",
                    models.CharField(
                        max_length=50, unique=True, verbose_name="Código do Equipamento"
                    ),
                ),
                (
                    "nome_equipamento",
                    models.CharField(
                        max_length=100, verbose_name="Nome do Equipamento"
                    ),
                ),
                (
                    "capacidade_minima",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        verbose_name="Capacidade de Medição Mínima",
                    ),
                ),
                (
                    "capacidade_maxima",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        verbose_name="Capacidade de Medição Máxima",
                    ),
                ),
                (
                    "observacoes_capacidade",
                    models.TextField(
                        blank=True, verbose_name="Observações sobre as Capacidades"
                    ),
                ),
                (
                    "resolucao",
                    models.DecimalField(
                        decimal_places=3, max_digits=10, verbose_name="Resolução"
                    ),
                ),
                (
                    "unidade_medida",
                    models.CharField(
                        choices=[
                            ("mm", "Milímetros"),
                            ("kg.cm", "Kilograma-centímetro"),
                            ("kgf", "Kilograma-força"),
                            ("°C", "Graus Celsius"),
                            ("UR", "Unidade Relativa"),
                            ("HCR", "HCR"),
                            ("HRB", "HRB"),
                        ],
                        max_length=10,
                        verbose_name="Unidade de Medida",
                    ),
                ),
                (
                    "tolerancia_total_minima",
                    models.DecimalField(
                        decimal_places=3,
                        max_digits=10,
                        verbose_name="Tolerância Total Mínima da Medida a Ser Realizada",
                    ),
                ),
                (
                    "frequencia_calibracao",
                    models.PositiveIntegerField(
                        verbose_name="Frequência de Calibração (meses)"
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="equipamentos",
            name="capacidade_maxima",
        ),
        migrations.RemoveField(
            model_name="equipamentos",
            name="capacidade_minima",
        ),
        migrations.RemoveField(
            model_name="equipamentos",
            name="frequencia_calibracao",
        ),
        migrations.RemoveField(
            model_name="equipamentos",
            name="resolucao",
        ),
        migrations.RemoveField(
            model_name="equipamentos",
            name="unidade_medida",
        ),
        migrations.AddField(
            model_name="equipamentos",
            name="status",
            field=models.CharField(
                choices=[("ativo", "Ativo"), ("inativo", "Inativo")],
                default="ativo",
                max_length=10,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="equipamentos",
            name="codigo",
            field=models.CharField(
                max_length=50, unique=True, verbose_name="Código do Equipamento"
            ),
        ),
        migrations.AlterField(
            model_name="equipamentos",
            name="fabricante",
            field=models.CharField(max_length=100, verbose_name="Fabricante"),
        ),
        migrations.AlterField(
            model_name="equipamentos",
            name="foto_equipamento",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="equipamentos/",
                verbose_name="Foto do Equipamento",
            ),
        ),
        migrations.AlterField(
            model_name="equipamentos",
            name="localizacao",
            field=models.CharField(max_length=100, verbose_name="Localização"),
        ),
        migrations.AlterField(
            model_name="equipamentos",
            name="modelo",
            field=models.CharField(max_length=100, verbose_name="Modelo"),
        ),
        migrations.AlterField(
            model_name="equipamentos",
            name="numero_serie",
            field=models.CharField(
                max_length=100, unique=True, verbose_name="Número de Série"
            ),
        ),
        migrations.AlterField(
            model_name="equipamentos",
            name="proprietario",
            field=models.CharField(max_length=100, verbose_name="Proprietário"),
        ),
        migrations.AlterField(
            model_name="equipamentos",
            name="responsavel",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="Funcionario.funcionario",
                verbose_name="Responsável",
            ),
        ),
        migrations.AlterField(
            model_name="equipamentos",
            name="tipo_instrumento",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="equipamentos",
                to="metrologia.tabelatecnica",
                verbose_name="Tipo de Instrumento",
            ),
        ),
    ]