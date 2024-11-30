
from .serializers import OrdersSerializer,UserSerializer,SMSerializer,PackingSerializer, LogoSerializer, FlyerSerializer, DairySerializer, InvitationSerializer, ProfileSerializer
from revo.models import Orders, SocialMediaImages, PackingImages, LogoImages, FlyerImages, DairyImages, InvitationImages, Clients
import random

from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model,authenticate
from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authentication import TokenAuthentication

import base64
import string
import random
import hashlib
import json
import requests
import uuid

from Crypto.Cipher import AES
from .paytm_checksum import PaytmChecksum


def get_auth_for_user(user):
    tokens = RefreshToken.for_user(user)
    return {
        'user': UserSerializer(user).data,
        'tokens': {
            'refresh': str(tokens),
            'access': str(tokens.access_token)
        }
    }

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'message': 'CSRF token set'})

def initiate_payment(request):
    if request.method == "POST":
        # Generate unique order ID
        order_id = str(uuid.uuid4())
        
        # Create dictionary with payment details
        paytm_params = {
            'MID': settings.PAYTM_MERCHANT_ID,
            'ORDER_ID': order_id,
            'TXN_AMOUNT': '100.00',  # Amount in string format
            'CUST_ID': 'CUST_001',  # Customer ID
            'INDUSTRY_TYPE_ID': settings.PAYTM_INDUSTRY_TYPE_ID,
            'WEBSITE': settings.PAYTM_WEBSITE,
            'CHANNEL_ID': settings.PAYTM_CHANNEL_ID,
            'CALLBACK_URL': 'http://192.168.1.2:8000/payment/response/',
        }

        # Generate checksum
        checksum = PaytmChecksum.generate_checksum(paytm_params, settings.PAYTM_MERCHANT_KEY)
        paytm_params['CHECKSUMHASH'] = checksum

        return render(request, 'payment.html', {
            'paytm_params': paytm_params,
            'paytm_url': settings.PAYTM_PAYMENT_GATEWAY_URL
        })

    return render(request, 'checkout.html')

@csrf_exempt
def payment_response(request):
    if request.method == "POST":
        received_data = dict(request.POST)
        paytm_params = {}
        
        for key, value in received_data.items():
            if key == 'CHECKSUMHASH':
                checksum = value[0]
            else:
                paytm_params[key] = value[0]

        # Verify checksum
        is_valid_checksum = PaytmChecksum.verify_checksum(
            paytm_params, settings.PAYTM_MERCHANT_KEY, checksum
        )

        if is_valid_checksum:
            if paytm_params['RESPCODE'] == '01':
                return HttpResponse("Payment Successful")
            else:
                return HttpResponse("Payment Failed")
        else:
            return HttpResponse("Checksum Verification Failed")

    return HttpResponse("Method Not Allowed", status=405)


class OrderCreateView(APIView):
    def post(self, request):
        data = request.data
        selected_options = request.get('options', [])
        total_amount = request.get('total_amount', 0)
        reference_images = request.get('reference_images', [])
        description = data.get('description', '')
        voice_messages = data.get('voice_message', [])
        payment_id = request.get("payment_id", None)

        orders = []
        for option in selected_options:
            order_data = {
                'checked_option': option,
                'total_amount': total_amount,
                'reference_images': reference_images,
                'description': description,
                'voice_messages': voice_messages,
                'payment_id': payment_id,
            }
            serializer = OrdersSerializer(data=order_data)
            if serializer.is_valid():
                serializer.save()
                orders.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(orders, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        orders = Orders.objects.all()
        serializer = OrdersSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        data = request.data
        try:
            # Update user fields
            user.first_name = data.get("first_name", user.first_name)
            user.last_name = data.get("last_name", user.last_name)
            user.email = data.get("email", user.email)
            user.save()

            # Serialize and return updated user data
            serializer = ProfileSerializer(user)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Requires authentication
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user
        try:
            client = Clients.objects.get(id=user.id)
            serializer = ProfileSerializer(client)
            return Response(serializer.data, status=200)
        except Clients.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        
class ClientSignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required"}, status=400)

        # Fetch user by email
        try:
            user = Clients.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)

        # Return user details
        user_data = {
            "name": user.username,
            "email": user.email,
        }
        return Response(user_data)
    
    def get(self, request):
        users = Clients.objects.all()
        serializers = UserSerializer(users, many = True)
        return Response(serializers.data, status=status.HTTP_200_OK)

class ClientRegistrationView(APIView):
    def post(self, request):
        data = request.data
        username = data.get("first_name")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        password = data.get("password")

        # Validate data
        if not username or not email or not password:
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        if Clients.objects.filter(email=email).exists():
            return Response({"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Create and save the client
        try:
            client = Clients.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=make_password(password)  # Hash the password before saving
            )
            client.save()
            return Response({"message": "Client registered successfully!"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   

class SMImagesList(ModelViewSet):
    queryset = SocialMediaImages.objects.all()
    serializer_class = SMSerializer

class PackingImagesList(ModelViewSet):
    queryset = PackingImages.objects.all()
    serializer_class = PackingSerializer

class LogoImagesList(ModelViewSet):
    queryset = LogoImages.objects.all()
    serializer_class = LogoSerializer

class FlyerImagesList(ModelViewSet):
    queryset = FlyerImages.objects.all()
    serializer_class = FlyerSerializer

class DairyImagesList(ModelViewSet):
    queryset = DairyImages.objects.all()
    serializer_class = DairySerializer

class InvitationImagesList(ModelViewSet):
    queryset = InvitationImages.objects.all()
    serializer_class = InvitationSerializer

