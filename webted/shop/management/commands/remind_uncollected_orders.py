from django.core.management.base import BaseCommand
from shop.models import Order
from shop.utils import send_line_message
from django.utils.timezone import localdate
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = "แจ้งเตือนลูกค้าที่ยังไม่มารับสินค้าในวันนัดหมาย"

    def handle(self, *args, **kwargs):
        today = localdate()
        orders = Order.objects.filter(status__in=["waiting_confirm", "approved"], pickup_date__lt=today)

        count = 0
        for order in orders:
            try:
                user = order.user
                if user.line_user_id:
                    message = (
                        f"📣 แจ้งเตือนยังไม่มารับสินค้า\n"
                        f"🧾 หมายเลขออเดอร์: #{order.id}\n"
                        f"📅 วันที่นัดรับ: {order.pickup_date}\n"
                        f"📍 กรุณาติดต่อเจ้าหน้าที่หากยังไม่ได้รับสินค้า"
                    )
                    send_line_message(user.line_user_id, message)
                    count += 1
            except ObjectDoesNotExist:
                continue

        self.stdout.write(self.style.SUCCESS(f"แจ้งเตือนแล้วทั้งหมด {count} รายการ"))