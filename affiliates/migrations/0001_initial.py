# Generated by Django 4.2.7 on 2025-04-10 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Affiliate',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('active', models.BooleanField(default=True)),
                ('social_media', models.URLField(blank=True, max_length=255, null=True)),
                ('promo_code', models.CharField(max_length=50, unique=True)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Afiliado',
                'verbose_name_plural': 'Afiliados',
            },
        ),
    ]
