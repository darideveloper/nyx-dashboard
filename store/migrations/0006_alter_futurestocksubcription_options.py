# Generated by Django 4.2.7 on 2024-07-22 20:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_rename_futurestocksusbcriptionuser_futurestocksubcription'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='futurestocksubcription',
            options={'verbose_name': 'Future Stock Subscription', 'verbose_name_plural': 'Future Stock Subscriptions'},
        ),
    ]
