# Generated by Django 4.2.16 on 2025-04-14 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qualidade_fornecimento", "0028_materiaprimacatalogo_tolerancia"),
    ]

    operations = [
        migrations.AddField(
            model_name="relatoriof045",
            name="alongamento",
            field=models.CharField(blank=True, default="N/A", max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="relatoriof045",
            name="escoamento",
            field=models.CharField(blank=True, default="N/A", max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="relatoriof045",
            name="estriccao",
            field=models.CharField(blank=True, default="N/A", max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="relatoriof045",
            name="resistencia_tracao",
            field=models.CharField(blank=True, default="N/A", max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="relatoriof045",
            name="torcao_certificado",
            field=models.CharField(blank=True, default="N/A", max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="relatoriof045",
            name="bitola",
            field=models.CharField(max_length=30),
        ),
    ]
