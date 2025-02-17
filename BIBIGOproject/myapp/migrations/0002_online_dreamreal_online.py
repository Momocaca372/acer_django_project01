# Generated by Django 5.1.4 on 2025-02-06 02:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Online",
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
                ("domain", models.CharField(max_length=30)),
            ],
            options={
                "db_table": "online",
            },
        ),
        migrations.AddField(
            model_name="dreamreal",
            name="online",
            field=models.ForeignKey(
                db_constraint=False,
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="myapp.online",
            ),
        ),
    ]
