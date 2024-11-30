from rest_framework import serializers
from revo.models import Orders,SocialMediaImages, PackingImages, LogoImages, FlyerImages, DairyImages, InvitationImages, Clients

class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Clients
        fields = ['username', 'email', 'first_name', 'last_name', 'thumbnail']



class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Clients
        fields = ['username', 'email', 'first_name', 'last_name', 'thumbnail']

class SMSerializer(serializers.ModelSerializer):

    class Meta:
        model = SocialMediaImages
        fields = '__all__'

class PackingSerializer(serializers.ModelSerializer):

    class Meta:
        model = PackingImages
        fields = '__all__'

class LogoSerializer(serializers.ModelSerializer):

    class Meta:
        model = LogoImages
        fields = '__all__'

class FlyerSerializer(serializers.ModelSerializer):

    class Meta:
        model = FlyerImages
        fields = '__all__'

class DairySerializer(serializers.ModelSerializer):

    class Meta:
        model = DairyImages
        fields = '__all__'

class InvitationSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvitationImages
        fields = '__all__'
