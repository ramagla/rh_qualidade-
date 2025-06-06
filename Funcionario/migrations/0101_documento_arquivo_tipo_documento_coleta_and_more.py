# Generated by Django 4.2.16 on 2025-05-12 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0100_rename_ivel_cargo_nivel"),
    ]

    operations = [
        migrations.AddField(
            model_name="documento",
            name="arquivo_tipo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("copia_fisica", "Cópia Física"),
                    ("copia_eletronica", "Cópia Eletrônica"),
                    ("copia_digitalizada", "Cópia Física / Cópia Digitalizada"),
                    ("pasta_az", "Cópia Física / Pasta A-Z"),
                    ("pasta_suspensa", "Cópia Física / Pasta Suspensa"),
                    (
                        "copia_eletronica_servidor",
                        "Cópia Eletrônica (Servidor / Sistema)",
                    ),
                    ("planilha_eletronica", "Planilha Eletrônica"),
                    ("numero", "Cópia Eletrônica / Número"),
                    ("copia_dupla", "Cópia Física / Cópia Eletrônica"),
                    ("copia_servidor", "Cópia Eletrônica / Servidor"),
                    (
                        "copia_az_fisica_eletronica",
                        "Cópia Eletrônica / Física / Pasta A-Z",
                    ),
                    ("papel", "Papel"),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="documento",
            name="coleta",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="documento",
            name="descarte",
            field=models.CharField(
                blank=True,
                choices=[
                    ("destruido", "Destruído"),
                    ("deletar", "Deletar"),
                    ("obsoleto", "Obsoleto"),
                    ("destruido_deletar", "Destruído / Deletar"),
                    ("apagar", "Deletar / Apagar"),
                    ("destruir", "Destruir"),
                ],
                max_length=30,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="documento",
            name="local_armazenamento",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="documento",
            name="recuperacao",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="documento",
            name="tempo_retencao",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
