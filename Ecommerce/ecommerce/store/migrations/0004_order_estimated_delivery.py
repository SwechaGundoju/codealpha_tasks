# Generated by Django 5.1.7 on 2025-03-13 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_alter_cart_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='estimated_delivery',
            field=models.DateField(blank=True, null=True),
        ),
    ]
