from django.urls import path, include
from rest_framework import routers
from . import views
from .views import UpdateToBeMadeAPIView, Preview_ImageAPIView, ViewOrdersAPIView, TransactionAPIView, CreateOrderAPIView, SMImagesList, PackingImagesList, LogoImagesList, FlyerImagesList, DairyImagesList, InvitationImagesList, ClientRegistrationView, ProfileView, ClientSignInView


router = routers.DefaultRouter()
router.register(r'revo/social', SMImagesList)
router.register(r'revo/packing', PackingImagesList)
router.register(r'revo/logo', LogoImagesList)
router.register(r'revo/flyer', FlyerImagesList)
router.register(r'revo/dairy', DairyImagesList)
router.register(r'revo/invitation', InvitationImagesList)

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('register/', ClientRegistrationView.as_view(), name='user-register'),
    path('sign_in/', ClientSignInView.as_view(), name='user-signIn'),
    #path('order_create/', OrderCreateView.as_view(), name='create-order'),#Working
    path('order/create/', CreateOrderAPIView.as_view(), name='create-order-api'),
    path('order/complete/', TransactionAPIView.as_view(), name='create-complete-api'),
    path('order/show/', ViewOrdersAPIView.as_view(), name='show-complete-api'),
    path('order/preview_image/', Preview_ImageAPIView.as_view(), name='show-preview-image'),
    path('order/submit-update/', UpdateToBeMadeAPIView.as_view(), name='update-To-preview-image'),

]