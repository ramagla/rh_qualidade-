# Generated by Django 4.2.16 on 2025-05-13 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0102_treinamento_necessita_avaliacao"),
    ]

    operations = [
        migrations.AddField(
            model_name="avaliacaotreinamento",
            name="anexo",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="avaliacoes_treinamento/",
                verbose_name="Comprovante/Anexo",
            ),
        ),
    ]
