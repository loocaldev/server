# Generated by Django 5.0.6 on 2024-11-16 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loocal', '0007_userprofile_is_temporary'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='phone_code',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
    ]
