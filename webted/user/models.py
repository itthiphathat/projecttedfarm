from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    line_user_id = models.CharField(max_length=50, unique=True, blank=True, null=True)  # ✅ เพิ่มฟิลด์นี้

    ROLE_CHOICES = [
        ('customer', 'ลูกค้า'),
        ('staff', 'พนักงาน'),
        ('admin', 'แอดมิน'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "full_name", "phone_number"]

    def __str__(self):
        return self.email
