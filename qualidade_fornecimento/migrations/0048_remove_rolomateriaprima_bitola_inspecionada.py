# Generated by Django 4.2.16 on 2025-04-17 17:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qualidade_fornecimento", "0047_rolomateriaprima_alongamento_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rolomateriaprima",
            name="bitola_inspecionada",
        ),
    ]
