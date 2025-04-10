import razorpay
import json
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages  # ✅ Import to clear old messages
from .models import Product, Cart, Order
from datetime import datetime, timedelta
from django.urls import reverse
from django.db.models import Q

# ✅ Homepage View
def homepage(request):
    cart_count = Cart.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    return render(request, "store/homepage.html", {"cart_count": cart_count})

# ✅ Product List View
def product_list(request):
    query = request.GET.get("q")  # ✅ Get the search query from the request
    products = Product.objects.all()

    if query:
        products = products.filter(Q(name__icontains=query))  # ✅ Search by product name

    cart_count = Cart.objects.filter(user=request.user).count() if request.user.is_authenticated else 0

    return render(request, 'store/product_list.html', {
        'products': products,
        'cart_count': cart_count,
        'query': query
    })

# ✅ Add to Cart
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(product=product, user=request.user)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart_view')

# ✅ View Cart
@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    cart_count = cart_items.count()
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'cart_count': cart_count})

# ✅ Remove from Cart
@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item = Cart.objects.filter(product=product, user=request.user).first()
    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart_view')

# ✅ Clear Cart
@login_required
def clear_cart(request):
    Cart.objects.filter(user=request.user).delete()
    messages.success(request, "Your cart has been cleared.")
    return redirect('cart_view')

# ✅ Checkout View (Fixed Address Handling & Cleared Old Messages)
@login_required
def checkout(request):
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in to place an order.")
        return redirect('login')

    # ✅ Clear old messages before checkout (Prevents old messages appearing)
    storage = get_messages(request)
    list(storage)  # Forces messages to be consumed, clearing them

    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == "POST":
        address = request.POST.get("address", "No address provided")

        order = Order.objects.create(
            user=request.user,
            name=request.user.username,
            email=request.user.email,
            address=address,  
            total_price=total_price,
            payment_status="Pending",
            estimated_delivery=datetime.now().date() + timedelta(days=5)  # ✅ Set delivery date
        )

        Cart.objects.filter(user=request.user).delete()
        messages.success(request, "Your order has been placed! Please complete the payment.")
        return redirect('payment_page', order_id=order.id)

    return render(request, "store/checkout.html", {"cart_items": cart_items, "total_price": total_price})

# ✅ Payment Page
@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    amount = max(int(order.total_price * 100), 100)  # Ensure minimum ₹1 (100 paisa)
    client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

    payment = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1",
    })

    context = {
        "order": order,
        "amount": amount,
        "payment": payment,
        "razorpay_key": settings.RAZORPAY_API_KEY
    }

    return render(request, "store/payment_page.html", context)

# ✅ Handle Payment Success (Fixed Missing Order Issue)
@login_required
def payment_success(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # ✅ Ensure order_id is present in data
            if not data or "order_id" not in data:
                return JsonResponse({"status": "Error", "message": "Invalid payment data"}, status=400)

            order_id = data.get("order_id")
            order = Order.objects.filter(id=order_id, payment_status="Pending").first()

            if order:
                order.payment_status = "Paid"
                order.save()

                subject = "Order Confirmed - Fashion Store"
                message = f"Hello {order.name},\n\nYour payment was successful! Your order will be delivered soon.\n\nThank you!"
                send_mail(subject, message, settings.EMAIL_HOST_USER, [order.email])

                redirect_url = reverse("order_confirmation", kwargs={"order_id": order.id})
                return JsonResponse({"redirect_url": redirect_url})

        except Exception as e:
            return JsonResponse({"status": "Error", "message": str(e)}, status=500)

    return JsonResponse({"status": "Payment Failed"}, status=400)

# ✅ Order Confirmation (Fixed Delivery Date Calculation)
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    estimated_delivery = order.created_at + timedelta(days=5)

    context = {
        "order": order,
        "user_name": request.user.get_full_name() or request.user.username,
        "estimated_delivery": estimated_delivery.strftime("%B %d, %Y"),
    }
    return render(request, "store/order_confirmation.html", context)

# ✅ View My Orders
@login_required
def my_orders(request):
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in to view your orders.")
        return redirect('login')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Set estimated delivery date if missing (5 days from order date)
    for order in orders:
        if not order.estimated_delivery:
            order.estimated_delivery = order.created_at + timedelta(days=5)
            order.save()

    return render(request, 'store/my_orders.html', {
        'orders': orders,
        'today': datetime.today().date()  # ✅ Pass today's date
    })

# ✅ User Registration (Fixed `register()` Issue)
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account has been created successfully!')
            return redirect('homepage')  # Redirect to homepage after signup
        else:
            messages.error(request, 'Error in registration. Please check your details.')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})
