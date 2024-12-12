from django.db import models
from django.contrib.auth.models import AbstractUser
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

EXPO_PUSH_API_URL = "https://exp.host/--/api/v2/push/send"

def upload_thumbnail(instance, filename):
    path = f'thumbnail/{instance.username}'
    extension = filename.split('.')[-1]
    if extension:
        path = path + '.' + extension
    return path


class Clients(AbstractUser):
    phone = models.CharField(max_length=15, null=True, blank=True)
    notification_token = models.TextField(null=True, blank=True)
    thumbnail = models.ImageField(
        upload_to=upload_thumbnail,
        null=True,
        blank=True
    )
    def __str__(self) -> str:
        return self.email


class Order(models.Model):
    STATUS_CHOICES = [
        (1, 'Designing'),
        (2, 'Testing'),
        (3, 'Correction'),
        (4, 'Delivered'),
    ]
    payment_id = models.CharField(max_length=100, verbose_name="Payment ID")
    order_id = models.CharField(max_length=100, verbose_name="Order ID")
    signature = models.CharField(max_length=100, verbose_name="Signature")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Signature")
    order_date = models.DateTimeField(auto_now_add=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name='orders')  # Link to the Clients model
    checked_option = models.CharField(max_length=255)  # To store the selected option
    description = models.TextField(null=True, blank=True)
    order_status = models.IntegerField(choices=STATUS_CHOICES, default=1)  # Default: Designing
    notificaation_token = models.TextField(null=True)
    
    preview_image = models.ImageField(upload_to='Preview_Image', null=True, blank=True)  # To store a single preview image URI
    delivery_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(null=True, default=False)

    reference_images = models.FileField(upload_to='reference_images/', null=True, blank=True)
    voice_messages = models.FileField(upload_to='voice_messages/', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Detect `order_status` changes
        if self.pk:
            original = Order.objects.get(pk=self.pk)
            if original.order_status != self.order_status:
                self.notify_status_change()  # Trigger notification if the status changes

        # Update `completed` field
        self.completed = self.order_status == 4
        super(Order, self).save(*args, **kwargs)

    def notify_status_change(self):
        status_text = dict(Order.STATUS_CHOICES).get(self.order_status, "Unknown Status")
        message = f"Your order '{self.order_id}' status has changed to: {status_text}"

        # Use the client's notification token if order token is not set
        token = self.notification_token or self.client.notification_token
        if not token:
            print(f"No notification token available for order {self.order_id}")
            return

        # Prepare notification payload
        payload = {
            "to": token,
            "title": "Order Status Update",
            "body": message,
            "data": {
                "order_id": self.order_id,
                "status": self.order_status,
            },
        }

        # Send the notification
        try:
            response = requests.post(EXPO_PUSH_API_URL, json=payload)
            response.raise_for_status()
            print(f"Notification sent for order {self.order_id}: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending notification for order {self.order_id}: {e}")
    
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