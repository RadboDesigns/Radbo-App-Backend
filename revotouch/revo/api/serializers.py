from rest_framework import serializers
from revo.models import Order,SocialMediaImages, PackingImages, LogoImages, FlyerImages, DairyImages, InvitationImages, Clients
from rest_framework.exceptions import ValidationError

class ViewOrderSerializers(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ['order_id', 'checked_option', 'order_date', 'delivery_date', 'order_status', 'preview_image']

class CreateOrderSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    currency = serializers.CharField(max_length=3)

    def validate_currency(self, value):
        supported_currencies = ['INR', 'USD']
        if value not in supported_currencies:
            raise serializers.ValidationError(f"Currency must be one of {supported_currencies}")
        return value

class TransactionModelserializers(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "payment_id",
            "order_id",
            "signature",
            "amount",
            "checked_option",
            "reference_images",
            "description",
            "voice_messages",
            "client",
        ]

    def validate_reference_images(self, value):
        if value.size > 5 * 1024 * 1024:  # 5 MB limit
            raise ValidationError("Reference image file size exceeds 5MB.")
        return value

    def validate_voice_messages(self, value):
        if value.size > 10 * 1024 * 1024:  # 10 MB limit
            raise ValidationError("Voice message file size exceeds 10MB.")
        return value


class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('order_date', 'order_status')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Clients
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'thumbnail']



class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Clients
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'thumbnail']

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
