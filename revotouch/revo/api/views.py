
from requests import request
from .serializers import ViewOrderSerializers, TransactionModelserializers, CreateOrderSerializer, OrdersSerializer,UserSerializer,SMSerializer,PackingSerializer, LogoSerializer, FlyerSerializer, DairySerializer, InvitationSerializer, ProfileSerializer
from revo.models import Order, SocialMediaImages, PackingImages, LogoImages, FlyerImages, DairyImages, InvitationImages, Clients
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
import json

from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model,authenticate
from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authentication import TokenAuthentication
from rest_framework import parsers

from revo.api.razorpy.main import RazorpayClient

rz_client = RazorpayClient()

def get_auth_for_user(user):
    tokens = RefreshToken.for_user(user)
    return {
        'user': UserSerializer(user).data,
        'tokens': {
            'refresh': str(tokens),
            'access': str(tokens.access_token)
        }
    }

@csrf_exempt
def save_push_token(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            token = data.get("token")
            email = data.get("email")  # Identify the client by email

            if not token or not email:
                return JsonResponse({"error": "Token and email are required."}, status=400)

            client = Clients.objects.get(email=email)
            client.notification_token = token
            client.save()

            return JsonResponse({"message": "Token saved successfully."})
        except Clients.DoesNotExist:
            return JsonResponse({"error": "Client not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method."}, status=400)

class ViewOrdersAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {"error": "Email is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            client = Clients.objects.get(email=email)
            orders = Order.objects.filter(client=client.id)
            
            if not orders.exists():
                return Response(
                    {"error": "No orders found for this client"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
            serializer = ViewOrderSerializers(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Clients.DoesNotExist:
            return Response(
                {"error": "Client not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            # Handle any other unexpected errors
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class CreateOrderAPIView(APIView):
    def post(self, request):
        print("Received data:", request.data)  # Debugging
        
        create_order_serializer = CreateOrderSerializer(data=request.data)
        if create_order_serializer.is_valid():
            try:
                order_response = rz_client.create_order(
                    amount=create_order_serializer.validated_data.get("amount"),
                    currency=create_order_serializer.validated_data.get("currency")
                )
                response = {
                    "status_code": status.HTTP_201_CREATED,
                    "message": "order_created",
                    "error": order_response
                }
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                print("Razorpay error:", str(e))
                return Response(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Razorpay error"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            print("Validation errors:", create_order_serializer.errors)  # Debugging
            response = {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "bad request",
                "Error": create_order_serializer.errors
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

class TransactionAPIView(APIView):
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]

    def post(self, request):
        try:
            # Validate payment signature
            print("Received payment data:", request.data)

            required_fields = ['razorpay_payment_id', 'razorpay_order_id', 'razorpay_signature', 'client']
            missing_fields = [field for field in required_fields if not request.data.get(field)]
            if missing_fields:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": f"Missing required fields: {', '.join(missing_fields)}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            rz_client.verify_payment_signature(
                razorpay_payment_id=request.data.get('razorpay_payment_id'),
                razorpay_order_id=request.data.get('razorpay_order_id'),
                razorpay_signature=request.data.get('razorpay_signature'),
            )

            client_email = request.data.get("client")
            try:
                client = Clients.objects.get(email=client_email)
            except Clients.DoesNotExist:
                return Response(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Client not found."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process other fields
            order_data = {
                "payment_id": request.data.get("razorpay_payment_id"),
                "order_id": request.data.get("razorpay_order_id"),
                "signature": request.data.get("razorpay_signature"),
                "amount": request.data.get("amount"),
                "checked_option": request.data.get("checked_option"),
                "description": request.data.get("description"),
                "client": client.id,
            }

            # Handle file uploads
            if 'images[0]' in request.FILES:
                order_data['reference_images'] = request.FILES.get('images[0]')
            
            if 'recordings[0]' in request.FILES:
                order_data['voice_messages'] = request.FILES.get('recordings[0]')

            # Save the order
            serializer = TransactionModelserializers(data=order_data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status_code": status.HTTP_201_CREATED, "message": "Transaction created"},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Invalid data", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {"status_code": status.HTTP_400_BAD_REQUEST, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileView(APIView):

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client = Clients.objects.get(email=email)
            serializer = ProfileSerializer(client)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Clients.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        
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
        phone = data.get("phone")
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
                phone = phone,
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



# @ensure_csrf_cookie
# def get_csrf_token(request):
#     return JsonResponse({'message': 'CSRF token set'})

# def initiate_payment(request):
#     if request.method == "POST":
#         # Generate unique order ID
#         order_id = str(uuid.uuid4())
        
#         # Create dictionary with payment details
#         paytm_params = {
#             'MID': settings.PAYTM_MERCHANT_ID,
#             'ORDER_ID': order_id,
#             'TXN_AMOUNT': '100.00',  # Amount in string format
#             'CUST_ID': 'CUST_001',  # Customer ID
#             'INDUSTRY_TYPE_ID': settings.PAYTM_INDUSTRY_TYPE_ID,
#             'WEBSITE': settings.PAYTM_WEBSITE,
#             'CHANNEL_ID': settings.PAYTM_CHANNEL_ID,
#             'CALLBACK_URL': 'http://192.168.1.2:8000/payment/response/',
#         }

#         # Generate checksum
#         checksum = PaytmChecksum.generate_checksum(paytm_params, settings.PAYTM_MERCHANT_KEY)
#         paytm_params['CHECKSUMHASH'] = checksum

#         return render(request, 'payment.html', {
#             'paytm_params': paytm_params,
#             'paytm_url': settings.PAYTM_PAYMENT_GATEWAY_URL
#         })

#     return render(request, 'checkout.html')

# @csrf_exempt
# def payment_response(request):
#     if request.method == "POST":
#         received_data = dict(request.POST)
#         paytm_params = {}
        
#         for key, value in received_data.items():
#             if key == 'CHECKSUMHASH':
#                 checksum = value[0]
#             else:
#                 paytm_params[key] = value[0]

#         # Verify checksum
#         is_valid_checksum = PaytmChecksum.verify_checksum(
#             paytm_params, settings.PAYTM_MERCHANT_KEY, checksum
#         )

#         if is_valid_checksum:
#             if paytm_params['RESPCODE'] == '01':
#                 return HttpResponse("Payment Successful")
#             else:
#                 return HttpResponse("Payment Failed")
#         else:
#             return HttpResponse("Checksum Verification Failed")

#     return HttpResponse("Method Not Allowed", status=405)