# Generated by Django 4.2.7 on 2024-07-16 21:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FutureStock',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('amount', models.IntegerField()),
                ('datetime', models.DateTimeField()),
                ('added', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Future Stock',
                'verbose_name_plural': 'Future Stocks',
            },
        ),
        migrations.RemoveField(
            model_name='status',
            name='id',
        ),
        migrations.AlterField(
            model_name='status',
            name='key',
            field=models.CharField(max_length=255, primary_key=True, serialize=False),
        ),
        migrations.AlterModelTable(
            name='status',
            table=None,
        ),
    ]
