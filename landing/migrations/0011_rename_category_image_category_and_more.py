# Generated by Django 4.2.7 on 2024-09-20 00:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0010_rename_category_image_category_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='image',
            old_name='Category',
            new_name='category',
        ),
        migrations.RenameField(
            model_name='text',
            old_name='Category',
            new_name='category',
        ),
        migrations.RenameField(
            model_name='video',
            old_name='Category',
            new_name='category',
        ),
    ]