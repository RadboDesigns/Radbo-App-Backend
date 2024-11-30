from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from .models import SocialMediaImages
# Create your views here.

def socialMediaUpdate(request):
    images = SocialMediaImages.objects.all()

    data = {'items': list(images.values())}
    return JsonResponse(data)
