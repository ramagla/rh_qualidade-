# Generated by Django 4.2.16 on 2025-06-12 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qualidade_fornecimento", "0083_alter_rolomateriaprima_nro_rolo"),
    ]

    operations = [
        migrations.AddField(
            model_name="controleservicoexterno",
            name="data_negociada",
            field=models.DateField(
                blank=True, null=True, verbose_name="Data Negociada"
            ),
        ),
    ]
