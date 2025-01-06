from django.db import models
from django.contrib.auth.models import AbstractUser
import requests
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings


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
    
    # New custom order ID field
    custom_order_id = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        verbose_name="Custom Order ID"
    )
    
    payment_id = models.CharField(max_length=100, verbose_name="Payment ID")
    order_id = models.CharField(max_length=100, verbose_name="Order ID")
    signature = models.CharField(max_length=100, verbose_name="Signature")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount")
    order_date = models.DateTimeField(auto_now_add=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name='orders')
    checked_option = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    order_status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    notification_token = models.TextField(null=True)
    preview_image = models.ImageField(upload_to='Preview_Image', null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(null=True, default=False)
    reference_images = models.FileField(upload_to='reference_images/', null=True, blank=True)
    voice_messages = models.FileField(upload_to='voice_messages/', null=True, blank=True)

    @staticmethod
    def generate_custom_order_id():
        """Generate the next custom order ID"""
        prefix = 'RADBO'
        # Get the last order with a custom_order_id
        last_order = Order.objects.filter(
            custom_order_id__startswith=prefix
        ).order_by('-custom_order_id').first()
        
        if last_order:
            try:
                # Extract the number from the last order ID
                last_number = int(last_order.custom_order_id[5:])
                next_number = last_number + 1
            except ValueError:
                # If there's any error parsing the number, start from 7000
                next_number = 7000
        else:
            # If no previous orders exist, start from 7000
            next_number = 7000
            
        return f'{prefix}{next_number}'

    def save(self, *args, **kwargs):
        if not self.custom_order_id:
            # Generate custom_order_id for new orders
            self.custom_order_id = self.generate_custom_order_id()
            
        if self.pk:
            try:
                original = Order.objects.get(pk=self.pk)
                if original.order_status != self.order_status:
                    self.notify_status_change(original.order_status)
            except Order.DoesNotExist:
                pass
        
        self.completed = self.order_status == 4
        super(Order, self).save(*args, **kwargs)

    def notify_status_change(self, previous_status=None):
        try:
            status_text = dict(Order.STATUS_CHOICES).get(self.order_status, "Unknown Status")
            previous_status_text = dict(Order.STATUS_CHOICES).get(previous_status, "Unknown Status")
            
            message = (
                f"Order Status Update: {self.custom_order_id}\n"  # Using custom_order_id instead of order_id
                f"Previous Status: {previous_status_text}\n"
                f"New Status: {status_text}"
            )

            token = self.notification_token or (self.client.notification_token if hasattr(self, 'client') else None)
            
            if not token:
                print(f"Warning: No notification token available for order {self.custom_order_id}")
                return

            payload = {
                "to": token,
                "title": f"Order {self.custom_order_id} Updated",  # Using custom_order_id
                "body": message,
                "data": {
                    "order_id": self.custom_order_id,  # Using custom_order_id
                    "previous_status": previous_status,
                    "new_status": self.order_status,
                    "status_text": status_text,
                    "type": "ORDER_STATUS_CHANGE"
                },
                "sound": "default",
                "priority": "high",
                "channelId": "order-updates"
            }

            print(f"Sending notification payload: {payload}")

            response = requests.post(
                "https://exp.host/--/api/v2/push/send",
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Accept-encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                }
            )
            
            print(f"Expo API Response: {response.status_code}")
            print(f"Expo API Response Content: {response.text}")
            
            response.raise_for_status()
            print(f"Notification sent successfully for order {self.custom_order_id}")
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to send notification for order {self.custom_order_id}: {str(e)}")
            print(f"Request details: {getattr(e.response, 'text', '')}")
        except Exception as e:
            print(f"Unexpected error sending notification for order {self.custom_order_id}: {str(e)}")

    def __str__(self):
        return self.custom_order_id
    
class ChangesOtUpdate(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE,
        related_name='updates'
    )
    description = models.TextField(null=True, blank=True)
    voice_messages = models.FileField(
        upload_to='update_voice_messages/', 
        null=True, 
        blank=True
    )
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update for Order {self.order.custom_order_id}"

    def get_custom_order_id(self):
        return self.order.custom_order_id
    get_custom_order_id = 'Custom Order ID'


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