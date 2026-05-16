from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models.functions import TruncDate, TruncMonth
from .models import Contact, Category, Product, Profile, Cart, ShippingAddress, Order, OrderItem, ProductSize, \
    ProductColor, Wishlist, Review

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Sum, Count

from .models import Order


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ('size', 'stock')


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = ('p_title',)
    inlines = [ProductSizeInline, ProductColorInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'size', 'color', 'quantity', 'price')
    readonly_fields = ('product', 'size', 'color', 'quantity', 'price')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'amount', 'paid', 'created_at')
    inlines = [OrderItemInline]


# Register to your custom admin site


class MyAdminSite(admin.AdminSite):
    site_header = "Shoe Store Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name="dashboard"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        # 📊 Basic Stats
        total_orders = Order.objects.count()
        total_revenue = Order.objects.aggregate(total=Sum('amount'))['total'] or 0

        from django.contrib.auth.models import User
        total_users = User.objects.count()

        # 📊 Orders per day (existing)
        from django.db.models.functions import TruncDate
        orders_by_date = (
            Order.objects
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
        )

        dates = [str(i['date']) for i in orders_by_date]
        counts = [i['count'] for i in orders_by_date]

        # 📊 Monthly Revenue
        monthly_data = (
            Order.objects
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('amount'))
        )

        months = [str(i['month'])[:7] for i in monthly_data]
        revenue = [float(i['total']) for i in monthly_data]

        # 🔥 Top Products
        top_products = (
            OrderItem.objects
            .values('product__p_title')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')[:5]
        )

        # 🧾 Recent Orders
        recent_orders = Order.objects.all().order_by('-created_at')[:5]

        context = dict(
            self.each_context(request),
            total_orders=total_orders,
            total_revenue=total_revenue,
            total_users=total_users,
            dates=dates,
            counts=counts,
            months=months,
            revenue=revenue,
            top_products=top_products,
            recent_orders=recent_orders,
        )

        return TemplateResponse(request, "admin/dashboard.html", context)


admin_site = MyAdminSite(name='myadmin')

admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(Wishlist)
admin_site.register(Contact)
admin_site.register(Category)
admin_site.register(Product, ProductAdmin)
admin_site.register(Profile)
admin_site.register(Cart)
admin_site.register(ShippingAddress)
admin_site.register(Order, OrderAdmin)
admin_site.register(OrderItem)

admin_site.register(Review)
