from django.contrib import admin
from .models import SocialMediaImages, PackingImages, LogoImages, FlyerImages, DairyImages, InvitationImages, Clients, Orders
# Register your models here.


admin.site.register(Clients)
admin.site.register(Orders)

admin.site.register(SocialMediaImages)
admin.site.register(PackingImages)
admin.site.register(LogoImages)
admin.site.register(FlyerImages)
admin.site.register(DairyImages)
admin.site.register(InvitationImages)

