# Generated by Django 4.2.7 on 2024-08-17 23:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_addon_colors_promocodes_set_sale'),
    ]

    operations = [
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Color',
                'verbose_name_plural': 'Colors',
            },
        ),
        migrations.RenameModel(
            old_name='Colors',
            new_name='ColorsNum',
        ),
        migrations.AlterModelOptions(
            name='colorsnum',
            options={'verbose_name': 'Colors Num', 'verbose_name_plural': 'Colors Num'},
        ),
        migrations.RemoveField(
            model_name='sale',
            name='colors_num',
        ),
        migrations.AddField(
            model_name='set',
            name='points',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='sale',
            name='color_set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='color_set', to='store.color'),
        ),
        migrations.AlterField(
            model_name='sale',
            name='logo_color_1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logo_color_1', to='store.color'),
        ),
        migrations.AlterField(
            model_name='sale',
            name='logo_color_2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logo_color_2', to='store.color'),
        ),
        migrations.AlterField(
            model_name='sale',
            name='logo_color_3',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logo_color_3', to='store.color'),
        ),
    ]
