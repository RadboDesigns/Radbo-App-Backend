
import razorpay
from requests import request
import requests
from .serializers import UpdateToBeMadeSerializers,Preview_ImageSerializers,ViewOrderSerializers, TransactionModelserializers, CreateOrderSerializer, OrdersSerializer,UserSerializer,SMSerializer,PackingSerializer, LogoSerializer, FlyerSerializer, DairySerializer, InvitationSerializer, ProfileSerializer
from revo.models import ChangesOtUpdate, Order, SocialMediaImages, PackingImages, LogoImages, FlyerImages, DairyImages, InvitationImages, Clients
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
import json
from decimal import Decimal
from django.db.models import Q  

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
import logging

logger = logging.getLogger(__name__)

rz_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

def get_auth_for_user(user):
    tokens = RefreshToken.for_user(user)
    return {
        'user': UserSerializer(user).data,
        'tokens': {
            'refresh': str(tokens),
            'access': str(tokens.access_token)
        }
    }


class UpdateToBeMadeAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def post(self, request):
        try:
            # Get order_id from request data
            order_id = request.data.get('order_id')
            if not order_id:
                return Response(
                    {"error": "Order ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Try to find order by both order_id and custom_order_id
            try:
                order = Order.objects.get(
                    Q(order_id=order_id) | 
                    Q(custom_order_id=order_id)
                )
            except Order.DoesNotExist:
                return Response(
                    {"error": "Order not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create the update
            update_data = {
                'order': order,
                'description': request.data.get('description', ''),
            }
            
            if 'voice_messages' in request.FILES:
                update_data['voice_messages'] = request.FILES['voice_messages']
            
            update = ChangesOtUpdate.objects.create(**update_data)
            
            # Return success response
            return Response(
                {
                    "message": "Update submitted successfully",
                    "data": {
                        "id": update.id,
                        "description": update.description,
                        "order_id": order.order_id,
                        "custom_order_id": order.custom_order_id
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            print(f"Error in UpdateToBeMadeAPIView: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class Preview_ImageAPIView(APIView):
    def post(self, request):
        order_id = request.data.get('order_id')
        print(f"Received order_id: {order_id}")  # Debug log
        
        if not order_id:
            return Response(
                {"error": "Order Id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            order = Order.objects.get(order_id=order_id)
            print(f"Found order: {order}")  # Debug log
            
            return Response({
                "preview_image": order.preview_image.url if order.preview_image else None
            }, status=status.HTTP_200_OK)
            
        except Order.DoesNotExist:
            print(f"Order not found for ID: {order_id}")  # Debug log
            return Response(
                {"error": "Order not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error processing request: {str(e)}")  # Debug log
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
@csrf_exempt
def save_token(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        token = data.get('token')
        email = data.get('email')
        
        print(f"Received token save request for email {email}")  # Debug log
        
        if not token or not email:
            return JsonResponse({
                'error': 'Both token and email are required'
            }, status=400)
        
        # Get or create client
        try:
            client = Clients.objects.get(email=email)
            print(f"Found existing client: {client.email}")  # Debug log
        except Clients.DoesNotExist:
            print(f"Client not found for email: {email}")  # Debug log
            return JsonResponse({'error': 'Client not found'}, status=404)
        
        # Update client token
        old_token = client.notification_token
        client.notification_token = token
        client.save()
        print(f"Updated client token from {old_token} to {token}")  # Debug log
        
        # Update active orders
        updated_orders = Order.objects.filter(
            client=client,
            completed=False
        ).update(notification_token=token)
        
        print(f"Updated {updated_orders} active orders with new token")  # Debug log
        
        # Verify updates
        orders = Order.objects.filter(client=client, completed=False)
        for order in orders:
            print(f"Order {order.order_id} now has token: {order.notification_token}")  # Debug log
        
        return JsonResponse({
            'status': 'success',
            'message': 'Token saved successfully',
            'orders_updated': updated_orders
        })
        
    except json.JSONDecodeError:
        print("Invalid JSON received")  # Debug log
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug log
        return JsonResponse({'error': str(e)}, status=500)

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
            orders = Order.objects.filter(client=client.id).order_by("-order_date")
            
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
        try:
            logger.info("Received order creation request: %s", request.data)
            
            create_order_serializer = CreateOrderSerializer(data=request.data)
            if not create_order_serializer.is_valid():
                logger.error("Validation errors: %s", create_order_serializer.errors)
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid request data",
                        "errors": create_order_serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract validated data
            amount = create_order_serializer.validated_data.get("amount")
            currency = create_order_serializer.validated_data.get("currency", "INR")

            # Validate amount
            if not isinstance(amount, (int, float, Decimal)) or amount <= 0:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid amount"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prepare order data
            order_data = {
                "amount": amount,
                "currency": currency,
                "payment_capture": 1  # Auto capture
            }
            
            logger.info("Creating Razorpay order with data: %s", order_data)
            
            try:
                # Correct method to create order in Razorpay
                order_response = rz_client.order.create(order_data)
                
                if not order_response or 'id' not in order_response:
                    logger.error("Invalid response from Razorpay: %s", order_response)
                    raise ValueError("Invalid response from Razorpay")
                
                logger.info("Order created successfully: %s", order_response['id'])
                
                return Response({
                    "status_code": status.HTTP_201_CREATED,
                    "message": "order_created",
                    "data": {
                        "order_id": order_response['id'],
                        "amount": order_response['amount']
                    }
                }, status=status.HTTP_201_CREATED)
                
            except razorpay.errors.BadRequestError as e:
                logger.error("Razorpay BadRequestError: %s", str(e))
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": f"Payment service validation error: {str(e)}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            except requests.exceptions.RequestException as e:
                logger.error("Razorpay request error: %s", str(e))
                return Response(
                    {
                        "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                        "message": "Payment service temporarily unavailable. Please try again."
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
        except Exception as e:
            logger.error("Unexpected error in order creation: %s", str(e), exc_info=True)
            return Response(
                {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An unexpected error occurred. Please try again later."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class TransactionAPIView(APIView):
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]

    def verify_payment_signature(self, payment_id, order_id, signature):
        try:
            rz_client.utility.verify_payment_signature({
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

    def post(self, request):
        try:
            logger.info("Starting transaction processing...")
            logger.info("Request data: %s", request.data)
            
            # Validate required fields
            required_fields = [
                'razorpay_payment_id',
                'razorpay_order_id',
                'razorpay_signature',
                'booking_details'
            ]
            
            missing_fields = [field for field in required_fields if field not in request.data]
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": f"Missing required fields: {', '.join(missing_fields)}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse booking_details first to handle potential JSON errors early
            booking_details = request.data.get('booking_details')
            try:
                if isinstance(booking_details, str):
                    booking_details = json.loads(booking_details)
                logger.info("Parsed booking details: %s", booking_details)
            except json.JSONDecodeError as e:
                logger.error("JSON decode error in booking_details: %s", str(e))
                return Response(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Invalid booking details format"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify payment signature
            payment_id = request.data.get('razorpay_payment_id')
            order_id = request.data.get('razorpay_order_id')
            signature = request.data.get('razorpay_signature')

            if not self.verify_payment_signature(payment_id, order_id, signature):
                logger.error("Payment signature verification failed")
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid payment signature"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify payment status
            try:
                payment = rz_client.payment.fetch(payment_id)
                logger.info("Payment status: %s", payment['status'])
                if payment['status'] != 'captured':
                    logger.error("Payment not captured. Status: %s", payment['status'])
                    return Response(
                        {
                            "status_code": status.HTTP_400_BAD_REQUEST,
                            "message": f"Payment not captured. Status: {payment['status']}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                logger.error("Error fetching payment: %s", str(e))
                return Response(
                    {
                        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": "Error verifying payment status"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Get client
            client_email = booking_details.get('email')
            if not client_email:
                logger.error("Client email missing from booking details")
                return Response(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Email is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                client = Clients.objects.get(email=client_email)
                logger.info("Found client with email: %s", client_email)
            except Clients.DoesNotExist:
                logger.error("Client not found with email: %s", client_email)
                return Response(
                    {"status_code": status.HTTP_404_NOT_FOUND, "message": "Client not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Prepare order data
            order_data = {
                "payment_id": payment_id,
                "order_id": order_id,
                "signature": signature,
                "amount": Decimal(payment['amount']) / 100,  # Convert from paisa to rupees
                "checked_option": ','.join(booking_details.get('options', [])),
                "description": booking_details.get('description', ''),
                "client": client.id,
            }
            logger.info("Prepared order data: %s", order_data)

            # Handle file uploads
            if 'images' in request.FILES:
                order_data['reference_images'] = request.FILES.getlist('images')[0]
                logger.info("Reference image added to order data")
            
            if 'recordings' in request.FILES:
                order_data['voice_messages'] = request.FILES.getlist('recordings')[0]
                logger.info("Voice message added to order data")

            # Create and save the order
            serializer = TransactionModelserializers(data=order_data)
            if serializer.is_valid():
                logger.info("Serializer validation passed")
                try:
                    transaction = serializer.save()
                    logger.info("Transaction saved successfully. ID: %s", transaction.id)
                    
                    return Response(
                        {
                            "status_code": status.HTTP_201_CREATED,
                            "message": "Transaction created successfully",
                            "data": {
                                "order_id": transaction.custom_order_id,
                                "amount": float(transaction.amount)
                            }
                        },
                        status=status.HTTP_201_CREATED
                    )
                except Exception as e:
                    logger.error("Error saving transaction: %s", str(e), exc_info=True)
                    return Response(
                        {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "message": "Error saving transaction to database"
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                logger.error("Serializer validation failed: %s", serializer.errors)
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid data",
                        "errors": serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error("Unexpected error: %s", str(e), exc_info=True)
            return Response(
                {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An unexpected error occurred"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
        phone = data.get("phone_number")
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