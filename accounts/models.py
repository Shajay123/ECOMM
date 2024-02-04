from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from base.emails import send_account_activation_email
from products.models import ColorVariant, Coupon, Product, SizeVariant


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_mail_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile')

    def get_cart_count(self):
        return CartItems.objects.filter(cart__is_paid = False ,cart__user = self.user).count



class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    razor_pay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razor_pay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razor_pay_payment_signature = models.CharField(max_length=100, null=True, blank=True)

    def get_cart_total(self):
        cart_items = self.cart_items.all()
        price = []

        for cart_item in cart_items:
            price.append(cart_item.get_product_price())

        total_price = sum(price)

        if self.coupon:
            if self.coupon.minimum_amount > total_price:
                total_price = max(0, total_price - self.coupon.discount_price)
            else:
                total_price = total_price - self.coupon.discount_price

        # Ensure the total_price is at least 1.00 INR
        total_price = max(1.00, total_price)

        return total_price
    
    
class CartItems(BaseModel):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,related_name="cart_items")
    product = models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,blank=True)
    color_variant=models.ForeignKey(ColorVariant, on_delete=models.SET_NULL,null =True)
    size_variant=models.ForeignKey(SizeVariant,on_delete=models.SET_NULL,null=True)

    def get_product_price(self):
        price = [self.product.price]

        if self.color_variant:
            color_variant_price = self.color_variant.price
            price.append(color_variant_price)
        if self.size_variant:
            size_variant_price = self.size_variant.price
            price.append(size_variant_price)
        return sum(price)

@receiver(post_save, sender=User)
def send_email_token(sender, instance, created, **kwargs):
    try:
        if created:
            
            email_token = str(uuid.uuid4()) 
            Profile.objects.create(user = instance , email_token = email_token) # Fix: Use uuid.uuid4() instead of uuid.uuid64()
            email = instance.email
            send_account_activation_email(email, email_token)

    except Exception as e:  # Fix: Use "Exception" instead of "Expection"
        print(e)
