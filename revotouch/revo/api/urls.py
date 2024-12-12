from django.urls import path, include
from rest_framework import routers
from . import views
from .views import ViewOrdersAPIView, TransactionAPIView, CreateOrderAPIView, SMImagesList, PackingImagesList, LogoImagesList, FlyerImagesList, DairyImagesList, InvitationImagesList, ClientRegistrationView, ProfileView, ClientSignInView


router = routers.DefaultRouter()
router.register(r'revo/social', SMImagesList)
router.register(r'revo/packing', PackingImagesList)
router.register(r'revo/logo', LogoImagesList)
router.register(r'revo/flyer', FlyerImagesList)
router.register(r'revo/dairy', DairyImagesList)
router.register(r'revo/invitation', InvitationImagesList)

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', ProfileView.as_view(), name='user-profile'),#Not Working
    path('register/', ClientRegistrationView.as_view(), name='user-register'),#Not Working
    path('sign_in/', ClientSignInView.as_view(), name='user-signIn'),#Working
    #path('order_create/', OrderCreateView.as_view(), name='create-order'),#Working
    path('order/create/', CreateOrderAPIView.as_view(), name='create-order-api'),#Working
    path('order/complete/', TransactionAPIView.as_view(), name='create-complete-api'),#Working
    path('order/show/', ViewOrdersAPIView.as_view(), name='show-complete-api'),#Working

   
]