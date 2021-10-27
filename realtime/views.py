from django.http.response import HttpResponse
from django.shortcuts import render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def Home(request):
    return render(request, "index.html")