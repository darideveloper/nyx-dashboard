# Generated by Django 4.2.7 on 2025-04-12 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('affiliates', '0004_alter_affiliate_promo_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='affiliate',
            name='balance',
            field=models.FloatField(default=0.0),
        ),
    ]
