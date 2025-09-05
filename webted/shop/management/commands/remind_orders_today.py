from django.core.management.base import BaseCommand
from shop.models import Order
from user.models import CustomUser
from shop.utils import send_line_message
from django.utils.timezone import localdate

class Command(BaseCommand):
    help = "แจ้งเตือนออเดอร์ที่ต้องส่งวันนี้ ให้แอดมิน"

    def handle(self, *args, **kwargs):
        today = localdate()
        orders = Order.objects.filter(status='approved', pickup_date=today)
        if not orders.exists():
            return

        message = "📋 รายการออเดอร์ที่ต้องส่งวันนี้:"
        for order in orders:
            message += f"\n- #{order.id} {order.user.full_name} เวลา {order.pickup_time}"

        admins = CustomUser.objects.filter(role='admin', line_user_id__isnull=False)
        for admin in admins:
            send_line_message(admin.line_user_id, message)