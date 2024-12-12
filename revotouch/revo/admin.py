from django.contrib import admin
from django.utils.html import format_html
from .models import SocialMediaImages, PackingImages, LogoImages, FlyerImages, DairyImages, InvitationImages, Clients, Order
# Register your models here.

admin.site.register(SocialMediaImages)
admin.site.register(PackingImages)
admin.site.register(LogoImages)
admin.site.register(FlyerImages)
admin.site.register(DairyImages)
admin.site.register(InvitationImages)
admin.site.register(Clients)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'client', 'amount', 'order_status', 'order_date', 'completed', 'preview_image']
    readonly_fields = ['display_reference_images', 'display_voice_messages']
    
    def display_reference_images(self, obj):
        if obj.reference_images:
            return format_html('<img src="{}" width="300"/>', obj.reference_images.url)
        return "No image uploaded"
    display_reference_images.short_description = 'Reference Images'

    def display_voice_messages(self, obj):
        if obj.voice_messages:
            return format_html('''
                <audio controls>
                    <source src="{}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
            ''', obj.voice_messages.url)
        return "No voice message uploaded"
    display_voice_messages.short_description = 'Voice Messages'

    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'payment_id', 'signature', 'amount', 'client', 'completed', 'preview_image')
        }),
        ('Order Details', {
            'fields': ('checked_option', 'description', 'order_status', 'delivery_date')
        }),
        ('Files', {
            'fields': ('reference_images', 'display_reference_images', 'voice_messages', 'display_voice_messages')
        }),
    )

