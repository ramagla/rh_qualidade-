# Generated by Django 4.2.16 on 2025-04-10 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qualidade_fornecimento", "0014_relacaomateriaprima_item_seguranca_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="materiaprimacatalogo",
            name="tipo_abnt",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Tipo ABNT"
            ),
        ),
    ]
