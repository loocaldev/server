# Generated by Django 5.0.6 on 2024-11-20 16:57

import loocal.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loocal', '0009_userprofile_birthdate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to=loocal.models.get_profile_picture_upload_path),
        ),
    ]