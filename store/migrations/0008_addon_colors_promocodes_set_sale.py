# Generated by Django 4.2.7 on 2024-08-02 23:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0007_rename_futurestocksubcription_futurestocksubscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='Addon',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Extra',
                'verbose_name_plural': 'Extras',
            },
        ),
        migrations.CreateModel(
            name='Colors',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('num', models.IntegerField()),
                ('price', models.FloatField()),
                ('details', models.TextField()),
            ],
            options={
                'verbose_name': 'Set',
                'verbose_name_plural': 'Sets',
            },
        ),
        migrations.CreateModel(
            name='PromoCodes',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=255)),
                ('discount', models.FloatField()),
            ],
            options={
                'verbose_name': 'Promo Code',
                'verbose_name_plural': 'Promo Codes',
            },
        ),
        migrations.CreateModel(
            name='Set',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('price', models.FloatField()),
                ('recommended', models.BooleanField(default=False)),
                ('logos', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Set',
                'verbose_name_plural': 'Sets',
            },
        ),
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('colors_num', models.IntegerField()),
                ('logo', models.ImageField(upload_to='')),
                ('full_name', models.CharField(max_length=255)),
                ('country', models.CharField(max_length=255)),
                ('state', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('postal_code', models.CharField(max_length=255)),
                ('street_address', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=255)),
                ('total', models.FloatField()),
                ('addons', models.ManyToManyField(to='store.addon')),
                ('color_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='color_set', to='store.colors')),
                ('logo_color_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logo_color_1', to='store.colors')),
                ('logo_color_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logo_color_2', to='store.colors')),
                ('logo_color_3', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logo_color_3', to='store.colors')),
                ('promo_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.promocodes')),
                ('set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.set')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sale',
                'verbose_name_plural': 'Sales',
            },
        ),
    ]