# Generated by Django 5.1.3 on 2024-12-11 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('revo', '0005_order_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='notificaation_token',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='preview_image',
            field=models.ImageField(blank=True, null=True, upload_to='Preview_Image'),
        ),
    ]
