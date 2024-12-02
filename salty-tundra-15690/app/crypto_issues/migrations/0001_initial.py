# Generated by Django 5.1.3 on 2024-11-30 06:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Repository",
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
                ("name", models.CharField(max_length=200)),
                ("owner", models.CharField(max_length=100)),
                ("url", models.URLField()),
                ("stars", models.IntegerField(default=0)),
                ("last_updated", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="CryptoIssue",
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
                ("title", models.CharField(max_length=300)),
                ("body", models.TextField()),
                ("issue_number", models.IntegerField()),
                ("created_at", models.DateTimeField()),
                ("updated_at", models.DateTimeField()),
                ("html_url", models.URLField()),
                ("labels", models.JSONField(default=list)),
                ("state", models.CharField(max_length=20)),
                (
                    "complexity",
                    models.CharField(
                        choices=[
                            ("beginner", "Beginner"),
                            ("intermediate", "Intermediate"),
                            ("advanced", "Advanced"),
                        ],
                        default="intermediate",
                        max_length=20,
                    ),
                ),
                (
                    "repository",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="crypto_issues.repository",
                    ),
                ),
            ],
        ),
    ]
