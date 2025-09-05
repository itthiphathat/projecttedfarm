from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser  

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="ชื่อผู้ใช้",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "กรอกชื่อผู้ใช้"}),
        help_text=""  
    )
    full_name = forms.CharField(
        max_length=255, required=True, label="ชื่อ-นามสกุล",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "กรอกชื่อ-นามสกุล"})
    )
    phone_number = forms.CharField(
        max_length=15, required=True, label="เบอร์โทร",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "กรอกเบอร์โทร"})
    )
    email = forms.EmailField(
        required=True, label="อีเมล",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "กรอกอีเมล"})
    )
    line_user_id = forms.CharField(  # ✅ เพิ่มฟิลด์ LINE User ID
        max_length=50, required=False, label="LINE User ID",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "LINE User ID (ถ้ามี)"})
    )
    password1 = forms.CharField(
        label="รหัสผ่าน",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "กรอกรหัสผ่าน"}),
        help_text="" 
    )
    password2 = forms.CharField(
        label="ยืนยันรหัสผ่าน",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "ยืนยันรหัสผ่าน"}),
        help_text="" 
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("❌ รหัสผ่านทั้งสองช่องต้องตรงกัน")

        return cleaned_data

    class Meta:
        model = CustomUser
        fields = ["username", "full_name", "phone_number", "email", "line_user_id", "password1", "password2"]

class EditProfileForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=255, required=True, label="ชื่อ-นามสกุล",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "กรอกชื่อ-นามสกุล"})
    )
    phone_number = forms.CharField(
        max_length=15, required=True, label="เบอร์โทร",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "กรอกเบอร์โทร"})
    )
    email = forms.EmailField(
        required=True, label="อีเมล",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "กรอกอีเมล"})
    )

    class Meta:
        model = CustomUser
        fields = ["full_name", "phone_number", "email"]


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        required=True, label="อีเมล",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "กรอกอีเมล"})
    )


class LoginForm(forms.Form):
    email = forms.EmailField(label='อีเมล')
    password = forms.CharField(label='รหัสผ่าน', widget=forms.PasswordInput)
