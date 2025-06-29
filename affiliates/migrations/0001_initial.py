# Generated by Django 4.2.7 on 2025-04-11 00:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0033_rename_stripe_link_sale_payment_link'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Affiliate',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('social_media', models.URLField(blank=True, help_text='Social media link for the affiliate (e.g., Instagram, Facebook)', max_length=255, null=True)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('promo_code_field', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='store.promocode', verbose_name='Código promocional')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='affiliate', to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Afiliado',
                'verbose_name_plural': 'Afiliados',
            },
        ),
    ]
