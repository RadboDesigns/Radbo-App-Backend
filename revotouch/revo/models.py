from django.db import models
from django.contrib.auth.models import AbstractUser

def upload_thumbnail(instance, filename):
    path = f'thumbnail/{instance.username}'
    extension = filename.split('.')[-1]
    if extension:
        path = path + '.' + extension
    return path


class Clients(AbstractUser):
    thumbnail = models.ImageField(
        upload_to=upload_thumbnail,
        null=True,
        blank=True
    )


class Orders(models.Model):
    STATUS_CHOICES = [
        (1, 'Designing'),
        (2, 'Testing'),
        (3, 'Correction'),
        (4, 'Delivered'),
    ]

    order_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name='orders')  # Link to the Clients model
    checked_option = models.CharField(max_length=255)  # To store the selected option
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_images = models.JSONField(null=True, blank=True)  # To store multiple image URIs as JSON
    description = models.TextField(null=True, blank=True)
    voice_messages = models.JSONField(null=True, blank=True)  # To store URIs of voice messages
    order_status = models.IntegerField(choices=STATUS_CHOICES, default=1)  # Default: Designing
    preview_image = models.URLField(max_length=500, null=True, blank=True)  # To store a single preview image URI
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    payment_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.checked_option}"
    
class SocialMediaImages(models.Model):
    image = models.ImageField(upload_to='social_media')
    title = models.CharField(max_length=255)
    
    def __str__(self):
        return self.title

class PackingImages(models.Model):
    image = models.ImageField(upload_to='packing')
    title = models.CharField(max_length=255)
    
    def __str__(self):
        return self.title

class LogoImages(models.Model):
    image = models.ImageField(upload_to='logo')
    title = models.CharField(max_length=255)
    
    def __str__(self):
        return self.title

class FlyerImages(models.Model):
    image = models.ImageField(upload_to='flyer')
    title = models.CharField(max_length=255)
    
    def __str__(self):
        return self.title

class DairyImages(models.Model):
    image = models.ImageField(upload_to='dairy')
    title = models.CharField(max_length=255)
    
    def __str__(self):
        return self.title

class InvitationImages(models.Model):
    image = models.ImageField(upload_to='invitation')
    title = models.CharField(max_length=255)
    
    def __str__(self):
        return self.title