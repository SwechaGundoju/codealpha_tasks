from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

# ✅ Product Model
class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')  # Upload images to 'media/products/'

    def __str__(self):
        return self.name

# ✅ Cart Model
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow guest users
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    # ✅ Total price for a cart item
    def get_total_price(self):
        return self.product.price * self.quantity

# ✅ Order Model
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    address = models.TextField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Paid', 'Paid')],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    estimated_delivery = models.DateField(null=True, blank=True)  # ✅ New field for estimated delivery date

    def save(self, *args, **kwargs):
        if not self.estimated_delivery:
            self.estimated_delivery = datetime.now().date() + timedelta(days=5)  # ✅ Default: 5 days after order
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} by {self.user.username if self.user else 'Guest'} - ₹{self.total_price}"
