# Generated by Django 4.2.7 on 2025-06-11 21:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0034_sale_invoice_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='invoice_file',
            field=models.FileField(blank=True, null=True, upload_to='invoice_files'),
        ),
    ]
