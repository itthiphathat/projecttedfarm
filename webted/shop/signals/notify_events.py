from django.db.models.signals import post_save
from django.dispatch import receiver
from shop.models import Order, Product
from shop.utils import send_line_message

@receiver(post_save, sender=Order)
def notify_order_approved(sender, instance, created, **kwargs):
    if not created and instance.status == 'approved':
        if instance.user.line_user_id:
            send_line_message(instance.user.line_user_id,
                f"✅ คำสั่งซื้อ #{instance.id} ของคุณได้รับการอนุมัติแล้ว\n📅 รับของวันที่ {instance.pickup_date} เวลา {instance.pickup_time}"
            )

@receiver(post_save, sender=Product)
def notify_new_product(sender, instance, created, **kwargs):
    if created or kwargs.get('update_fields'):
        from user.models import CustomUser
        msg = f"🆕 สินค้าใหม่เข้าแล้ว: {instance.name}\n📦 พร้อมให้สั่งซื้อในระบบแล้ว!"
        users = CustomUser.objects.filter(role='customer', line_user_id__isnull=False)
        for u in users:
            send_line_message(u.line_user_id, msg)