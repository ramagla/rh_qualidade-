# Generated by Django 4.2.16 on 2025-06-24 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qualidade_fornecimento", "0088_alter_inspecao10_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inspecao10",
            name="observacoes",
            field=models.TextField(blank=True, verbose_name="Observações"),
        ),
    ]
