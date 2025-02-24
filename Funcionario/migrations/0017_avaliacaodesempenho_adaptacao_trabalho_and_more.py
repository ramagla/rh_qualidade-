# Generated by Django 5.1.2 on 2024-10-25 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "Funcionario",
            "0016_remove_avaliacaodesempenho_avaliacao_global_avaliado_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="avaliacaodesempenho",
            name="adaptacao_trabalho",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="avaliacaodesempenho",
            name="capacidade_aprendizagem",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="avaliacaodesempenho",
            name="interesse",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="avaliacaodesempenho",
            name="relacionamento_social",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
