# from tkinter.constants import CASCADE
from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify

from django.db import models
from django.contrib.auth.models import User


class Contact(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=10)
    message = models.TextField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Category(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Product(models.Model):
    p_title = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    product_image = models.ImageField(upload_to='products/', blank=True, null=True)

    p_description = models.TextField(max_length=500, blank=True, null=True)
    p_price = models.FloatField(max_length=10, blank=True, null=True)
    is_trending = models.BooleanField(default=False)

    slug = models.SlugField(blank=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.p_title)
            slug = base_slug
            counter = 1

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.p_title

    class Meta:
        db_table = 'products'


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="colors")
    color_name = models.CharField(max_length=50)
    color_image = models.ImageField(upload_to='products/colors/')

    def __str__(self):
        return f"{self.product.p_title} - {self.color_name}"


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.IntegerField()
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.p_title} - Size {self.size}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.IntegerField()
    color = models.ForeignKey(
        "ProductColor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    color_image = models.ImageField(upload_to="cart_colors/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.product}"

    class Meta:
        unique_together = ('user', 'product', 'size')


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100, unique=True)

    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    amount = models.IntegerField()
    paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_id


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    size = models.IntegerField()
    color = models.ForeignKey(ProductColor, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.FloatField()  # price at time of purchase

    def __str__(self):
        return f"{self.product.p_title} ({self.quantity})"


class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=200)

    phone = models.CharField(max_length=10)
    email = models.EmailField(null=True, blank=True)
    country = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.p_title}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    name = models.CharField(max_length=100)
    email = models.EmailField()
    comment = models.TextField()
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.p_title
