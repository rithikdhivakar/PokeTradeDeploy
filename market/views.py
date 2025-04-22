from django.shortcuts import render, redirect
from django.contrib import messages

def market_home(request):
    return render(request, 'market/market_home.html')