from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm, EditProfileForm, EmailAuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from user.models import CustomUser
from user.forms import LoginForm

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  
            user.line_user_id = form.cleaned_data.get("line_user_id") or None  
            user.save()  
            messages.success(request, "สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")
            return redirect("login")  
        else:
            print(form.errors)  # ✅ Debug: แสดงข้อผิดพลาดของฟอร์มใน Terminal
    else:
        form = CustomUserCreationForm()
    return render(request, "user/register.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=email, password=password)  

            if user is not None:
                login(request, user)
                messages.success(request, "เข้าสู่ระบบสำเร็จ!")

                if user.role in ['admin', 'staff']:
                    return redirect("admin_dashboard")
                return redirect("product_list")
            else:
                messages.error(request, "อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    else:
        form = LoginForm()
    return render(request, "user/login.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("product_list")

@login_required
def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "แก้ไขโปรไฟล์สำเร็จ!")
            return redirect("user:edit_profile")
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, "user/edit_profile.html", {"form": form})

@login_required
def manage_users(request):
    if request.user.role not in ['admin', 'staff']:
        return redirect('admin-dashboard')

    users = CustomUser.objects.all()
    return render(request, 'user/list_users.html', {'users': users})

@login_required
def edit_user(request, user_id):
    if request.user.role not in ['admin', 'staff']:
        return redirect('admin-dashboard')

    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        role = request.POST.get('role')
        if role in ['customer', 'staff', 'admin']:
            user.role = role
            user.save()
        return redirect('user:manage_users')

    return render(request, 'user/edit_user.html', {'user': user})

from django.shortcuts import redirect
from django.conf import settings
import urllib.parse

def line_login(request):
    base_url = "https://access.line.me/oauth2/v2.1/authorize"
    params = {
        "response_type": "code",
        "client_id": settings.LINE_CHANNEL_ID,
        "redirect_uri": settings.LINE_REDIRECT_URI,
        "state": "123abc",  # สุ่มก็ได้
        "scope": "openid profile",
        "bot_prompt": "aggressive"
    }
    login_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(login_url)

import requests
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import login
from user.models import CustomUser  # เปลี่ยนตาม project

def line_callback(request):
    code = request.GET.get("code")
    token_url = "https://api.line.me/oauth2/v2.1/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.LINE_REDIRECT_URI,
        "client_id": settings.LINE_CHANNEL_ID,
        "client_secret": settings.LINE_CHANNEL_SECRET
    }

    res = requests.post(token_url, headers=headers, data=data)
    access_token = res.json().get("access_token")

    # ดึงโปรไฟล์
    profile = requests.get("https://api.line.me/v2/profile", headers={
        "Authorization": f"Bearer {access_token}"
    }).json()

    line_user_id = profile["userId"]
    display_name = profile["displayName"]

    # หา user เดิม หรือสร้างใหม่
    user, _ = CustomUser.objects.get_or_create(
        line_user_id=line_user_id,
        defaults={"full_name": display_name, "role": "customer"}
    )
    login(request, user)
    return redirect("product_list")

