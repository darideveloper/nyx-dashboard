# Generated by Django 4.2.7 on 2024-07-16 21:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_futurestock_remove_status_id_alter_status_key_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='status',
            options={'verbose_name': 'Status', 'verbose_name_plural': 'Status'},
        ),
    ]
