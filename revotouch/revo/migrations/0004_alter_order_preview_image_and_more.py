# Generated by Django 5.1.3 on 2024-12-07 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('revo', '0003_clients_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='preview_image',
            field=models.ImageField(default=0, upload_to='Preview_Image'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='order',
            name='reference_images',
            field=models.FileField(blank=True, null=True, upload_to='reference_images/'),
        ),
        migrations.AlterField(
            model_name='order',
            name='voice_messages',
            field=models.FileField(blank=True, null=True, upload_to='voice_messages/'),
        ),
    ]
