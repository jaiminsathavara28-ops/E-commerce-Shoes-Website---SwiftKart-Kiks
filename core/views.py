from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.models import Contact, ShippingAddress, OrderItem, ProductSize, Wishlist, ProductColor, Review
from .models import Category, Product, Cart
from django.contrib.auth.models import User
from .models import Profile
from django.db.models import Q, Avg, Count

from .models import Order
import razorpay
from django.conf import settings
import uuid
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# Create your views here.
def index(request):
    #  Our Products (normal latest products)
    products = Product.objects.all()[:3]

    #  Trending Products
    trending_products = Product.objects.filter(is_trending=True)

    #  fallback if no trending
    if not trending_products.exists():
        trending_products = Product.objects.exclude(id__in=products).order_by('-id')[:4]

    return render(request, "index.html", {
        "products": products,
        "trending_products": trending_products
    })


def about_us(request):
    return render(request, 'about-us.html')


def blog(request):
    return render(request, 'blog.html')


def blog_details(request):
    return render(request, 'blog-details.html')


def add_to_wishlist(request, id):
    product = Product.objects.get(id=id)

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect('wishlist')


@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)

    total_price = 0
    for item in cart_items:
        item.total = item.product.p_price * item.quantity
        total_price += item.total

    total = 0
    for item in cart_items:
        total += item.product.p_price * item.quantity

    # GST Calculation (Example 18%)
    gst = total * 0.18
    grand_total = total + gst

    context = {

    }

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'total': total,
        'gst': gst,
        'grand_total': grand_total,
    })


def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    quantity = int(request.POST.get('quantity', 1))
    size = request.POST.get('size')
    color_id = request.POST.get('color')
    color_image = request.POST.get("color_image")

    if not request.user.is_authenticated:
        return redirect('signin')
    # Check if size selected
    if not size:
        messages.error(request, "Please select size")
        return redirect('product_details', id=product.id, slug=product.slug)

    # Get stock for selected size
    product_size = get_object_or_404(ProductSize, product=product, size=size)

    # Check stock
    if quantity > product_size.stock:
        messages.error(request, "Not enough stock available")
        return redirect('product_details', id=product.id, slug=product.slug)

    if color_id:
        color = get_object_or_404(ProductColor, id=color_id)
    else:
        color = None

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        size=size,
        color=color,
    )

    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity

    cart_item.color_image = color_image
    cart_item.save()

    Wishlist.objects.filter(
        user=request.user,
        product=product
    ).delete()
    return redirect('cart')


@login_required
def remove_from_cart(request, id):
    cart_item = Cart.objects.get(id=id, user=request.user)
    cart_item.delete()
    return redirect('cart')


#
# def checkout(request):
#     return render(request, 'checkout.html')


def contact_us(request):
    if request.method == "POST":
        first_name = request.POST['name']
        last_name = request.POST['lname']
        email = request.POST['email']
        message = request.POST['message']

        c = Contact.objects.create(first_name=first_name, last_name=last_name, email=email, message=message)
    return render(request, 'contact-us.html')


def shop(request):
    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            Category.objects.create(name=name)
        return redirect('shop')

    categories = Category.objects.all()
    products = Product.objects.all()

    # ✅ CATEGORY FILTER
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # ✅ SEARCH
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(p_title__icontains=query) |
            Q(p_description__icontains=query)
        )

    # ✅ PRICE FILTER
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price and max_price:
        products = products.filter(
            p_price__gte=min_price,
            p_price__lte=max_price
        )

    # ✅ PAGINATION
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'shop.html', {
        'categories': categories,
        'page_obj': page_obj,  # 👈 use this in template
        'selected_category': int(category_id) if category_id else None
    })


def quick_view(request, id):
    product = Product.objects.get(id=id)

    data = {
        "id": product.id,
        "name": product.p_title,
        "price": str(product.p_price),
        "desc": product.p_description,
        "image": product.product_image.url if product.product_image else ""
    }

    return JsonResponse(data)


def wishlist(request):
    items = Wishlist.objects.filter(user=request.user)

    return render(request, "wishlist.html", {"items": items})


def signin(request):
    # if request.user.is_authenticated:
    #     return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login  successfully!")
            return redirect('index')

        else:
            messages.warning(request, "bad credential")
            return redirect('signin')
    return render(request, 'login.html')


def signup(request):
    context = {
        'genders': ['Male', 'Female'],
    }

    if request.method == 'POST':
        username = request.POST.get('username')
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        dob = request.POST.get('birthday')
        pass1 = request.POST.get('password')
        pass2 = request.POST.get('cpassword')

        #  Check password match
        if pass1 != pass2:
            messages.error(request, "Passwords do not match")
            return redirect('signup')

        #  Username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('signup')

        #  Email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('signup')

        try:
            #  Validate password BEFORE creating user
            validate_password(pass1)

        except ValidationError as e:
            for error in e:
                messages.error(request, error)
            return redirect('signup')

        #  Create user (ONLY ONCE)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=pass1
        )

        user.first_name = fname
        user.last_name = lname
        user.save()

        #  Create profile
        Profile.objects.create(
            user=user,
            gender=gender,
            phone=phone,
            city=city,
            dob=dob
        )

        login(request, user)

        messages.success(request, "Account created & logged in successfully!")

        return redirect('index')

    return render(request, 'signup.html', context)


def signout(request):
    logout(request)
    messages.success(request, "Logout successfully.")
    return redirect('signin')


def update_quantity(request):
    if request.method == "POST":
        cart_id = request.POST.get("cart_id")
        action = request.POST.get("action")

        cart_item = get_object_or_404(Cart, id=cart_id)

        if action == "increase":
            cart_item.quantity += 1
        elif action == "decrease":
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart_item.delete()
                return JsonResponse({"deleted": True})

        cart_item.save()

        cart_items = Cart.objects.filter(user=cart_item.user)
        total = sum(item.product.p_price * item.quantity for item in cart_items)
        grand_total = total + (total * 0.18)

        return JsonResponse({
            "quantity": cart_item.quantity,
            "item_total": cart_item.product.p_price * cart_item.quantity,
            "grand_total": grand_total
        })
    return None


@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)

    subtotal = sum(item.product.p_price * item.quantity for item in cart_items)
    gst = subtotal * 0.18
    grand_total = subtotal + gst

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        country = request.POST.get("country")
        state = request.POST.get("state")
        city = request.POST.get("city")
        address = request.POST.get("address")

        # Save shipping
        ShippingAddress.objects.create(
            user=request.user,
            name=name,
            email=request.user.email,
            phone=phone,
            country=country,
            state=state,
            city=city,
            address=address,
        )

        # Save total in session for payment page
        request.session["grand_total"] = float(grand_total)

        return redirect("payment")

    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "gst": gst,
        "grand_total": grand_total,
        "user_data": request.user,
    }

    return render(request, "checkout.html", context)


@login_required
def payment(request):
    grand_total = request.session.get("grand_total")

    if not grand_total:
        return redirect("checkout")

    amount = int(float(grand_total) * 100)

    payment = client.order.create({
        "amount": "amount",
        "currency": "INR",
        "payment_capture": "1"
    })

    # Create order
    order = Order.objects.create(
        user=request.user,
        order_id=str(uuid.uuid4()),
        amount=grand_total,
        razorpay_order_id=payment["id"],
        paid=False
    )

    # Get latest shipping address
    shipping = ShippingAddress.objects.filter(user=request.user).last()

    # Link shipping to order
    if shipping:
        shipping.order = order
        shipping.save()

    context = {
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order_id": payment["id"],
        "amount": amount,
    }

    return render(request, "payment.html", context)


@csrf_exempt
def payment_success(request):
    if request.method == "POST":

        print("Payment Success View Triggered")

        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_payment_id = request.POST.get("razorpay_payment_id")

        order = Order.objects.get(razorpay_order_id=razorpay_order_id)

        if not order.paid:
            order.paid = True
            order.razorpay_payment_id = razorpay_payment_id
            order.save()

            cart_items = Cart.objects.filter(user=order.user)
            print("Cart Count:", cart_items.count())

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.p_price,
                    size=item.size,
                    color=item.color if item.color else None
                )

                # Reduce stock based on size
                product_size = ProductSize.objects.get(
                    product=item.product,
                    size=item.size
                )

                product_size.stock -= item.quantity
                product_size.save()

            cart_items.delete()

        shipping = ShippingAddress.objects.filter(user=order.user).last()

        return render(request, "payment-success.html", {
            "order": order,
            "shipping": shipping
        })

    return redirect("checkout")


@login_required
def account_dashboard(request):
    return render(request, 'dashboard.html')


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "my-orders.html", {"orders": orders})


@login_required
def invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    shipping = ShippingAddress.objects.filter(order=order).first()
    return render(request, "invoice.html", {"order": order, "shipping": shipping})


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    elements = []
    styles = getSampleStyleSheet()

    # ================= HEADER =================
    elements.append(Paragraph("<b>SWIFTKART KIKS STORE</b>", styles['Title']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>INVOICE</b>", styles['Heading2']))
    elements.append(Spacer(1, 20))

    # ================= ORDER DETAILS =================
    elements.append(Paragraph(f"Order ID: {order.order_id}", styles['Normal']))
    elements.append(Paragraph(f"Payment ID: {order.razorpay_payment_id}", styles['Normal']))
    elements.append(Paragraph(f"Order Date: {order.created_at.strftime('%d %B %Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # ================= CUSTOMER DETAILS =================
    shipping = ShippingAddress.objects.filter(order=order).first()

    elements.append(Paragraph("<b>Customer Details</b>", styles['Heading3']))

    if shipping:
        elements.append(Paragraph(f"Name: {shipping.name}", styles['Normal']))
        elements.append(Paragraph(f"Email: {request.user.email}", styles['Normal']))
        elements.append(Paragraph(f"Phone: {shipping.phone}", styles['Normal']))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("<b>Shipping Address</b>", styles['Heading3']))
        elements.append(Paragraph(
            f"{shipping.address}, {shipping.city}, {shipping.state}, {shipping.country}",
            styles['Normal']
        ))
    else:
        elements.append(Paragraph("Shipping address not available", styles['Normal']))

    elements.append(Spacer(1, 30))

    # ================= PRODUCT TABLE =================
    data = [["Product", "Size", "Color", "Qty", "Price", "Total"]]
    total_amount = 0

    items = OrderItem.objects.filter(order=order)

    for item in items:
        product_name = item.product.p_title if item.product else "Product Removed"

        total = item.quantity * item.price
        total_amount += total

        data.append([
            Paragraph(product_name, styles['Normal']),  # ✅ wrap
            Paragraph(str(item.size), styles['Normal']),
            Paragraph(str(item.color) if item.color else "-", styles['Normal']),
            item.quantity,
            f"₹{item.price}",
            f"₹{total}"
        ])

    table = Table(data, colWidths=[200, 70, 90, 50, 70, 80])

    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),

        # Alignment
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 30))

    # ================= TOTAL =================
    subtotal = total_amount
    gst = subtotal * 0.18
    grand_total = subtotal + gst

    elements.append(Paragraph(f"Subtotal : ₹{subtotal:.2f}", styles['Normal']))
    elements.append(Paragraph(f"GST (18%): ₹{gst:.2f}", styles['Normal']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f"<b>Total Amount: ₹{grand_total:.2f}</b>",
        styles['Heading3']
    ))

    elements.append(Spacer(1, 40))

    # ================= FOOTER =================
    elements.append(Paragraph(
        "Thank you for shopping with SwiftKart Kiks!",
        styles['Normal']
    ))

    elements.append(Paragraph(
        "Support: support@shoestore.com",
        styles['Normal']
    ))

    # ================= BUILD PDF =================
    doc.build(elements)

    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=Invoice_{order.order_id}.pdf'

    return response


def product_details(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug)
    sizes = ProductSize.objects.filter(product=product)

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        comment = request.POST.get("comment")
        rating = int(request.POST.get("rating", 0))

        if name and email and comment and rating:
            Review.objects.create(
                product=product,
                name=name,
                email=email,
                comment=comment,
                rating=rating
            )

        return redirect('product_details', id=product.id, slug=product.slug)

    #  Safe query
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    total_reviews = reviews.aggregate(count=Count('id'))['count']

    return render(request, "product-details.html", {
        "product": product,
        "sizes": sizes,
        "reviews": reviews,
        "range_5": [1, 2, 3, 4, 5],
        'avg_rating': round(avg_rating, 1),
        'total_reviews': total_reviews
    })


def user_login(request):
    logout(request)  # 🔥 force logout previous session

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, "login.html", {
                "error": "Invalid username or password"
            })

        login(request, user)
        return redirect("home")

    return render(request, "login.html")


def category_products(request, category):
    products = Product.objects.filter(category__name__iexact=category)
    return render(request, 'shop.html', {'products': products, 'category': category})


@login_required
def edit_profile(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")

        profile.phone = request.POST.get("phone")
        profile.city = request.POST.get("city")

        user.save()
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("account_dashboard")

    return render(request, "edit-profile.html", {
        "user": user,
        "profile": profile
    })
