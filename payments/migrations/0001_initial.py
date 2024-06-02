# Generated by Django 5.0.6 on 2024-06-02 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('token', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('installments', models.IntegerField()),
                ('payment_method_id', models.CharField(max_length=100)),
                ('payer_email', models.EmailField(max_length=254)),
                ('status', models.CharField(default='pending', max_length=50)),
            ],
        ),
    ]
