# Generated by Django 5.0.6 on 2024-11-15 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loocal', '0003_userprofile_document_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='reset_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
