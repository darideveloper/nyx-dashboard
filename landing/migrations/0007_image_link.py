# Generated by Django 4.2.7 on 2024-07-05 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0006_alter_video_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='link',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]
