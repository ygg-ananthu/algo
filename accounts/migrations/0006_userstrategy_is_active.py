# Generated by Django 5.1.6 on 2025-03-01 16:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_strategy_userstrategy"),
    ]

    operations = [
        migrations.AddField(
            model_name="userstrategy",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
