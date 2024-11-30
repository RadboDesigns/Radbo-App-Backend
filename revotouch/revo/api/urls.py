from django.urls import path, include
from rest_framework import routers
from . import views
from .views import OrderCreateView, SMImagesList, PackingImagesList, LogoImagesList, FlyerImagesList, DairyImagesList, InvitationImagesList, ClientRegistrationView, ProfileView, ClientSignInView, UpdateProfileView


router = routers.DefaultRouter()
router.register(r'revo/social', SMImagesList)
router.register(r'revo/packing', PackingImagesList)
router.register(r'revo/logo', LogoImagesList)
router.register(r'revo/flyer', FlyerImagesList)
router.register(r'revo/dairy', DairyImagesList)
router.register(r'revo/invitation', InvitationImagesList)

urlpatterns = [
    path('', include(router.urls)),
    path('update_profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('register/', ClientRegistrationView.as_view(), name='user-register'),
    path('sign_in/', ClientSignInView.as_view(), name='user-signIn'),
    path('order_create/', OrderCreateView.as_view(), name='create-order'),
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment/response/', views.payment_response, name='payment_response'),
    path('get-csrf-token//', views.get_csrf_token, name='get_csrf_token'),
]