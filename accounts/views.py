from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.urls import reverse
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from .forms import *

def index(request):
    return render(request, 'accounts/index.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if 'login' in request.POST:
            # Xử lý đăng nhập
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, 'Đăng nhập thành công!')
                return redirect('/')  # Chuyển về trang chủ
            else:
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng!')
        
        elif 'signup' in request.POST:
            # Xử lý đăng ký
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Tên đăng nhập đã tồn tại!')
            else:
                user = User.objects.create_user(username=username, password=password)
                user.save()
                return redirect('signup_success')
    
    return render(request, 'accounts/login.html')

def signup_success(request):
    return render(request, 'accounts/signup_success.html')