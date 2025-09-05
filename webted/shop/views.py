from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, CartItem, Order, OrderItem  
from .forms import ProductForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from user.models import CustomUser  
from shop.utils import send_line_message  
from django.utils import timezone 

User = get_user_model()

# ✅ แสดงสินค้า
def product_list(request):
    products = Product.objects.annotate(
        approved_sales=Count("order_items", filter=Q(order_items__order__status="approved"))
    )
    return render(request, 'shop/product_list.html', {'products': products})

@login_required
def mark_order_completed(request, order_id):
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, "คุณไม่มีสิทธิ์")
        return redirect('admin_order_list')

    order = get_object_or_404(Order, id=order_id)

    if order.status != "approved":
        messages.warning(request, "ต้องอนุมัติก่อนถึงจะบันทึกว่า 'มารับแล้ว'")
        return redirect('admin_order_list')

    order.status = "completed"
    order.save()

    messages.success(request, f"📦 ออเดอร์ #{order.id} ถูกบันทึกว่า 'มารับแล้ว'")
    return redirect('admin_order_list')



# ✅ 2. Dashboard สำหรับแอดมิน

@login_required
def admin_dashboard(request):
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('product_list')

    products = Product.objects.all()
    form = ProductForm()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.image = request.FILES.get('image')

            if product.quantity <= 0:
                messages.error(request, "กรุณาระบุจำนวนสินค้ามากกว่า 0")
                return redirect('admin_dashboard')

            product.save()
            messages.success(request, "เพิ่มสินค้าสำเร็จแล้ว!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "กรุณากรอกข้อมูลให้ถูกต้อง")
                    # แจ้งลูกค้าเมื่อมีสินค้าใหม่
            msg = (
            f"🆕 สินค้าเข้าใหม่: {product.name}\n"
            f"📦 จำนวน: {product.quantity} กิโลกรัม\n"
            f"🛒 รีบสั่งซื้อได้เลยผ่านระบบ!"
        )
        customers = CustomUser.objects.filter(role='customer', line_user_id__isnull=False)
        for u in customers:
            send_line_message(u.line_user_id, msg)

                # แจ้งลูกค้าเมื่อมีสินค้าใหม่
            msg = (
            f"🔄 มีการอัปเดตสินค้า: {product.name}\n"
            f"📦 คงเหลือปัจจุบัน: {product.quantity} กิโลกรัม\n"
            f"ℹ️ ดูรายละเอียดเพิ่มเติมและสั่งซื้อผ่านระบบได้เลย!"
        )
        customers = CustomUser.objects.filter(role='customer', line_user_id__isnull=False)
        for u in customers:
            send_line_message(u.line_user_id, msg)

    return render(request, 'shop/admin_dashboard.html', {'products': products, 'form': form})


# ✅ 3. ฟังก์ชันจัดการสินค้า (แก้ไข/ลบ)
@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('admin_dashboard')

@login_required

def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
                        # แจ้งลูกค้าเมื่อมีการแก้ไขสินค้า
        msg = f"🔄 สินค้าอัปเดต: {product.name}\n📦 มีการเปลี่ยนแปลงข้อมูลสินค้า ลองเข้าไปดูรายละเอียดเพิ่มเติมในระบบได้เลย!"
        customers = CustomUser.objects.filter(role='customer', line_user_id__isnull=False)
        for u in customers:
            send_line_message(u.line_user_id, msg)

            return redirect('admin_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'shop/edit_product.html', {'form': form, 'product': product})

# ✅ 4. ฟังก์ชันจัดการตะกร้าสินค้า
@login_required
def cart_detail(request):
    cart = get_or_create_cart(request.user)
    items = cart.items.select_related('product')
    total = sum(item.product.price * item.quantity for item in items)
    return render(request, 'shop/cart_detail.html', {'cart': cart, 'items': items, 'total': total})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    if product.quantity < quantity:
        messages.error(request, f"สินค้าในสต็อกมีเพียง {product.quantity} กิโลกรัมเท่านั้น")
        return redirect('product_list')

    cart = get_or_create_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    product.quantity -= quantity
    product.save()
    messages.success(request, "เพิ่มสินค้าเข้าไปในตะกร้าสำเร็จ!")
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.product.quantity += cart_item.quantity
    cart_item.product.save()
    cart_item.delete()
    messages.success(request, "ลบสินค้าออกจากตะกร้าสำเร็จ!")
    return redirect('cart')


@login_required
def checkout(request):
    if request.method == 'POST':
        cart = get_or_create_cart(request.user)
        items = cart.items.select_related('product')

        if not items.exists():
            messages.error(request, "ตะกร้าสินค้าว่างเปล่า")
            return redirect('cart_detail')

        # ✅ สร้างคำสั่งซื้อใหม่
        order = Order.objects.create(user=request.user)

        # ✅ สร้าง OrderItem ก่อนล้างตะกร้า
        order_items = []
        for item in items:
            order_item = OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            order_items.append(order_item)

        cart.items.all().delete()  # ✅ ล้างตะกร้า หลังจากสร้าง OrderItem เสร็จแล้ว


        return redirect('order_success', order_id=order.id)

    return redirect('cart_detail')

from django.shortcuts import render, redirect
from .models import Cart, CartItem, Order, OrderItem

def order_success(request):
    """ แสดงหน้าสรุปคำสั่งซื้อ (ยังไม่สร้าง Order) """
    cart = Cart.objects.get(user=request.user)  # ✅ ดึงตะกร้าของผู้ใช้
    cart_items = CartItem.objects.filter(cart=cart)  # ✅ ดึงรายการสินค้าในตะกร้า

    if not cart_items.exists():
        return redirect("cart")  # ถ้าตะกร้าว่าง ให้กลับไปที่ตะกร้า

    total_price = sum(item.product.price * item.quantity for item in cart_items)  # ✅ ใช้ CartItem

    context = {
        "items": cart_items,  # ✅ ส่ง CartItem ไปที่ Template
        "total_price": total_price
    }
    return render(request, "shop/order_success.html", context)  # ✅ ระบุ path เต็ม


def get_admin_user_id():
    """ ดึง user_id ของแอดมินจากฐานข้อมูล """
    admin = User.objects.filter(is_staff=True).first()  # ✅ ดึง Admin คนแรกที่มีอยู่
    return admin.line_user_id if admin and admin.line_user_id else None  # ✅ ต้องมี field `line_user_id` ในฐานข้อมูล

def confirm_order(request):
    if request.method == "POST":
        cart = get_or_create_cart(request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            messages.error(request, "❌ ตะกร้าสินค้าว่างเปล่า กรุณาเลือกสินค้า")
            return redirect("cart")

        pickup_date = request.POST.get("pickup_date")
        pickup_time = request.POST.get("pickup_time")
        payment_slip = request.FILES.get("payment_slip")
        comment = request.POST.get("comment", "")

        if not pickup_date or not pickup_time or not payment_slip:
            messages.error(request, "❌ กรุณากรอกข้อมูลให้ครบถ้วน")
            return redirect("order_success")

        # ✅ สร้าง Order ใหม่
        order = Order.objects.create(
            user=request.user,
            total_price=0,
            pickup_date=pickup_date,
            pickup_time=pickup_time,
            payment_slip=payment_slip,
            comment=comment,
            status="waiting_confirm"
        )

        total = 0
        for item in cart_items:
            product = item.product

            # ✅ เช็กสินค้าใกล้หมด (เทียบกับจำนวนก่อนสั่ง)
            if product.quantity < 20:
                message = (
                    f"⚠️ สินค้าใกล้หมด!\n"
                    f"📦 {product.name}\n"
                    f"เหลือเพียง {product.quantity} กิโลกรัม\n"
                    f"กรุณาตรวจสอบหรือเติมสินค้า"
                )
                admins = CustomUser.objects.filter(role='admin', line_user_id__isnull=False)
                for admin in admins:
                    send_line_message(admin.line_user_id, message)

                staffs = CustomUser.objects.filter(role='staff', line_user_id__isnull=False)
                for staff in staffs:
                    send_line_message(staff.line_user_id, message)

            # ✅ บันทึกลง OrderItem
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price=product.price
            )
            total += product.price * item.quantity

        order.total_price = total
        order.save()
        cart_items.delete()

        messages.success(request, "✅ คำสั่งซื้อของคุณถูกส่งเรียบร้อยแล้ว! กรุณารอการยืนยัน")

        # ✅ แจ้งลูกค้า
        if order.user.line_user_id:
            item_list = "\n".join([f"• {item.product.name} x {item.quantity} กก." for item in order.items.all()])
            send_line_message(order.user.line_user_id,
                f"🧾 คำสั่งซื้อ #{order.id} ของคุณถูกส่งเรียบร้อยแล้ว!\n📦 รายการ:\n{item_list}\n\nกรุณารอการอนุมัติจากเจ้าหน้าที่")

        # สร้างข้อความแสดงรายการสินค้า
        items_text = ""
        order_items = order.items.all()
        for i in order_items:
            items_text += f"\n- {i.product.name} {i.quantity} กิโล"

        notify_message = (
            f"📥 คำสั่งซื้อใหม่!\n"
            f"👤 ลูกค้า: {order.user.full_name}\n"
            f"🧾 หมายเลขออเดอร์: #{order.id}\n"
            f"💸 ยอดรวม: {order.total_price} บาท\n"
            f"📅 วันที่รับของ: {order.pickup_date} เวลา {order.pickup_time}\n"
            f"📦 รายการสินค้า:{items_text}"
        )

        for person in CustomUser.objects.filter(role__in=['admin', 'staff'], line_user_id__isnull=False):
            send_line_message(person.line_user_id, notify_message)

        return redirect("payment_status")



# ฟังก์ชันตรวจสอบสถานะคำสั่งซื้อ
@login_required
def payment_status(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    for order in orders:
        order.total_price = sum(item.quantity * item.price for item in order.items.all())
    return render(request, 'shop/payment_status.html', {'orders': orders})

#ฟังก์ชันช่วยเหลือเกี่ยวกับตะกร้า
def get_or_create_cart(user):
    return Cart.objects.get_or_create(user=user)[0]

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == "POST":
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity < 1:
            cart_item.delete()  # ถ้าปรับจำนวนเป็น 0 ให้ลบสินค้าออกจากตะกร้า
        else:
            # ตรวจสอบว่าสินค้าในสต็อกพอหรือไม่
            if new_quantity > cart_item.product.quantity + cart_item.quantity:
                messages.error(request, f"สินค้าในสต็อกมีเพียง {cart_item.product.quantity} ชิ้นเท่านั้น")
                return redirect('cart')  # เปลี่ยนจาก 'cart_detail' เป็น 'cart'
            difference = new_quantity - cart_item.quantity
            if difference > 0 and difference > cart_item.product.quantity:
                messages.error(request, f"สินค้าในสต็อกมีเพียง {cart_item.product.quantity} ชิ้นเท่านั้น")
                return redirect('cart')  # เปลี่ยนจาก 'cart_detail' เป็น 'cart'

            cart_item.product.quantity -= difference
            cart_item.product.save()

            cart_item.quantity = new_quantity
            cart_item.save()

        messages.success(request, "อัปเดตจำนวนสินค้าในตะกร้าสำเร็จ!")
    return redirect('cart')  # เปลี่ยนจาก 'cart_detail' เป็น 'cart'


@login_required
def upload_payment_slip(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST" and request.FILES.get('payment_slip'):
        order.payment_slip = request.FILES['payment_slip']
        order.status = "waiting_confirm"  # เปลี่ยนสถานะเป็นรออนุมัติ
        order.save()
        messages.success(request, "อัปโหลดสลิปการชำระเงินสำเร็จ!")


        return redirect('payment_status')
    
    return render(request, 'shop/upload_payment_slip.html', {'order': order})

from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Order

@login_required
def order_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # ให้ลูกค้าเห็นออเดอร์ของตัวเอง แม้ว่าจะยังไม่ได้รับการอนุมัติ
    return render(request, "shop/order_complete.html", {"order": order})


from django.db.models import Case, When, IntegerField

@login_required

def admin_order_list(request):
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('product_list')
    """แสดงรายการคำสั่งซื้อทั้งหมด เรียงลำดับให้คำสั่งซื้อที่ยังไม่ได้อนุมัติอยู่บนสุด
    และเรียงตามวันเวลาที่มารับสินค้า"""

    orders = Order.objects.all().order_by(
        Case(
            When(status="waiting_confirm", then=0),
            When(status="approved", then=1),
            When(status="rejected", then=2),
            When(status="completed", then=3),
            default=4, output_field=IntegerField(),
        ),
        "pickup_date",  # ✅ เรียงตามวันที่รับสินค้า (เก่าสุด -> ใหม่สุด)
        "pickup_time",  # ✅ เรียงตามเวลารับสินค้า (เช้า -> เย็น)
    )

    return render(request, 'shop/admin_order_list.html', {'orders': orders})


@login_required

def admin_confirm_payment(request, order_id):
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('product_list')
    order = get_object_or_404(Order, id=order_id)

    if order.status != "waiting_confirm":
        messages.error(request, "คำสั่งซื้อนี้ไม่สามารถอนุมัติได้")
        return redirect("admin_order_list")

    if request.method == "POST":
        order.status = "approved"
        order.save()

        # ✅ เพิ่มยอดขายของสินค้าที่อนุมัติแล้ว
        for item in order.items.all():
            item.product.sold_quantity += item.quantity
            item.product.save()

        # ✅ แจ้งลูกค้า
        if order.user.line_user_id:
            message = (
                f"🎉 คำสั่งซื้อของคุณได้รับการอนุมัติแล้ว!\n"
                f"🧾 หมายเลข: #{order.id}\n"
                f"📅 วันที่รับ: {order.pickup_date} เวลา {order.pickup_time}\n"
                f"💬 สถานะ: พร้อมให้ไปรับตามกำหนด"
            )
            send_line_message(order.user.line_user_id, message)

        # ✅ แจ้งพนักงาน
        staffs = CustomUser.objects.filter(role='staff', line_user_id__isnull=False)
        for staff in staffs:
            item_list = "\n".join([f"• {item.product.name} x {item.quantity} กก." for item in order.items.all()])
            message = (
                f"🎉 คำสั่งซื้อ #{order.id} ได้รับการอนุมัติแล้ว!\n"
                f"📦 รายการ:\n{item_list}\n"
                f"📅 กรุณามารับสินค้าที่จุดรับของในวันที่ {order.pickup_date} เวลา {order.pickup_time}\n"
                f"🤝 ขอบคุณที่ใช้บริการ!"
            )

            send_line_message(staff.line_user_id, message)

        messages.success(request, f"✅ อนุมัติคำสั่งซื้อ #{order.id} และอัปเดตยอดขายเรียบร้อย")
        return redirect("admin_order_list")

    return render(request, "shop/admin_confirm_payment.html", {"order": order})


@login_required

def admin_reject_payment(request, order_id):
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('product_list')
    """ฟังก์ชันสำหรับแอดมินเพื่อปฏิเสธการชำระเงิน"""
    
    order = get_object_or_404(Order, id=order_id)

    if order.status != "waiting_confirm":
        messages.error(request, "คำสั่งซื้อนี้ไม่สามารถปฏิเสธได้")
        return redirect('admin_order_list')

    if request.method == "POST":
        order.status = "rejected"
        order.save()

        messages.warning(request, f"❌ ปฏิเสธการชำระเงินสำหรับ Order #{order.id}")

        # ✅ แจ้งลูกค้า
        if order.user.line_user_id:
            message = (
                f"❌ คำสั่งซื้อของคุณถูกปฏิเสธ\n"
                f"🧾 หมายเลข: #{order.id}\n"
                f"💬 กรุณาติดต่อเจ้าหน้าที่หรือลองสั่งใหม่อีกครั้ง"
            )
            send_line_message(order.user.line_user_id, message)

        # ✅ แจ้งพนักงาน
        staffs = CustomUser.objects.filter(role='staff', line_user_id__isnull=False)
        for staff in staffs:
            message = (
                f"🚫 ปฏิเสธคำสั่งซื้อ\n"
                f"📦 หมายเลขออเดอร์: #{order.id}\n"
                f"👤 ลูกค้า: {order.user.full_name}\n"
                f"📝 สถานะ: ยกเลิกแล้ว"
            )
            send_line_message(staff.line_user_id, message)

        return redirect('admin_order_list')

    return render(request, 'shop/admin_reject_payment.html', {'order': order})


@login_required
def set_pickup_date(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        pickup_date = request.POST.get("pickup_date")
        pickup_time = request.POST.get("pickup_time")
        comment = request.POST.get("comment")
        payment_slip = request.FILES.get("payment_slip")

        if not pickup_date or not pickup_time or not payment_slip:
            messages.error(request, "กรุณาเลือกวันและเวลารับสินค้า และอัปโหลดสลิปโอนเงิน")
            return redirect('order_success', order_id=order_id)

        order.pickup_date = pickup_date
        order.pickup_time = pickup_time
        order.comment = comment
        order.payment_slip = payment_slip
        order.status = "waiting_confirm"
        order.save()

        messages.success(request, "✅ คำสั่งซื้อของคุณถูกส่งเรียบร้อยแล้ว!")
        return redirect('payment_status')

    return render(request, 'shop/order_success.html', {'order': order})



from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.http import JsonResponse

@login_required

def admin_sales_chart(request):
    if request.user.role not in ['admin']:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('product_list')
    return render(request, 'shop/admin_sales_chart.html')

from collections import defaultdict
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.db.models import Sum, F
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse
from .models import OrderItem

def sales_data(request):
    if request.user.role not in ['admin', 'staff']:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    range_type = request.GET.get("range", "day")

    # ใช้ trunc ตามช่วงเวลา
    if range_type == "week":
        trunc = TruncWeek("order__created_at")
    elif range_type == "month":
        trunc = TruncMonth("order__created_at")
    else:
        trunc = TruncDay("order__created_at")

    # กรองข้อมูลเฉพาะช่วงเวลาล่าสุด
    now = timezone.now()
    if range_type == "month":
        start_date = now - relativedelta(months=11)
    elif range_type == "day":
        start_date = now - relativedelta(days=29)
    elif range_type == "week":
        start_date = now - relativedelta(weeks=11)
    else:
        start_date = now - relativedelta(months=12)

    raw_data = (
        OrderItem.objects
        .filter(order__status__in=["approved", "completed"], order__created_at__gte=start_date)
        .annotate(period=trunc)
        .values("period", "product__name")
        .annotate(total=Sum(F("price") * F("quantity")))
        .order_by("period")
    )

    labels = sorted(set(item["period"].strftime("%Y-%m-%d") for item in raw_data))
    product_totals = defaultdict(lambda: {label: 0 for label in labels})

    for item in raw_data:
        date_str = item["period"].strftime("%Y-%m-%d")
        product_name = item["product__name"]
        product_totals[product_name][date_str] += float(item["total"])

    datasets = []
    for product, values in product_totals.items():
        datasets.append({
            "label": product,
            "data": [values[label] for label in labels]
        })

    total_all = sum(sum(v for v in product.values()) for product in product_totals.values())

    return JsonResponse({
        "labels": labels,
        "datasets": datasets,
        "total": total_all
    })


import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from user.models import CustomUser
from shop.utils import send_line_message  
from django.contrib.auth import get_user_model
User = get_user_model()

@csrf_exempt
def line_webhook(request):
    if request.method != "POST":
        return JsonResponse({"status": "invalid method"}, status=400)

    body = json.loads(request.body.decode("utf-8"))
    events = body.get("events", [])

    for event in events:
        if event.get("type") == "message":
            user_id = event["source"]["userId"]
            message_text = event["message"]["text"].strip()

            # ✅ ถ้าพิมพ์เบอร์โทร เช่น 0812345678
            phone = message_text

            # ✅ ค้นหาผู้ใช้ในระบบจากเบอร์
            user = User.objects.filter(phone_number=phone).first()

            if user:
                user.line_user_id = user_id
                user.save()

                send_line_message(user_id, f"✅ ผูกบัญชีเรียบร้อย คุณคือ {user.role.upper()}")
            else:
                send_line_message(user_id, "❌ ไม่พบเบอร์นี้ในระบบ กรุณาติดต่อแอดมิน")

    return JsonResponse({"status": "ok"})

from django.shortcuts import render

def privacy_policy(request):
    return render(request, "shop/privacy_policy.html")

def terms_of_use(request):
    return render(request, "shop/terms_of_use.html")
