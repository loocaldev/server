# Generated by Django 5.0.6 on 2024-11-16 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loocal', '0006_userprofile_is_email_verified_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_temporary',
            field=models.BooleanField(default=False),
        ),
    ]
