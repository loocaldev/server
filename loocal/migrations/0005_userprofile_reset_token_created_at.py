# Generated by Django 5.0.6 on 2024-11-15 22:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loocal', '0004_userprofile_reset_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='reset_token_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]