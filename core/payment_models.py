"""
Payment Gateway Integration Models
Supports Stripe and Razorpay for automated billing
"""
from django.db import models
from django.utils import timezone
from .models import Tenant, MemberProfile, Subscription


class PaymentGateway(models.Model):
    """Payment gateway configuration per tenant"""
    GATEWAY_CHOICES = (
        ('stripe', 'Stripe'),
        ('razorpay', 'Razorpay'),
        ('paypal', 'PayPal'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payment_gateways')
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    
    # Encrypted credentials (use django-encrypted-model-fields in production)
    api_key = models.CharField(max_length=255, help_text="Public/Publishable Key")
    api_secret = models.CharField(max_length=255, help_text="Secret Key")
    webhook_secret = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_test_mode = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_gateways'
        unique_together = ['tenant', 'gateway_type']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.get_gateway_type_display()}"


class SubscriptionPayment(models.Model):
    """Track all subscription payments"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Digital Wallet'),
        ('cash', 'Cash'),
    )
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='subscription_payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Gateway information
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    gateway_payment_id = models.CharField(max_length=255, blank=True)
    gateway_order_id = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Retry logic for failed payments
    retry_count = models.IntegerField(default=0)
    next_retry_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    invoice_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_payments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['member', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payment_date']),
        ]
    
    def __str__(self):
        return f"{self.member.user.username} - {self.amount} {self.currency} - {self.status}"
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        if not self.invoice_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            count = SubscriptionPayment.objects.filter(
                created_at__date=datetime.now().date()
            ).count() + 1
            self.invoice_number = f"INV-{date_str}-{count:04d}"
            self.save()
        return self.invoice_number


class PaymentMethod(models.Model):
    """Saved payment methods for members"""
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='payment_methods')
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE)
    
    # Gateway-specific customer/payment method IDs
    gateway_customer_id = models.CharField(max_length=255, help_text="Stripe customer ID or Razorpay customer ID")
    gateway_payment_method_id = models.CharField(max_length=255, blank=True)
    
    payment_type = models.CharField(max_length=20, choices=SubscriptionPayment.PAYMENT_METHOD_CHOICES)
    
    # Card details (last 4 digits only for display)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    card_expiry_month = models.IntegerField(null=True, blank=True)
    card_expiry_year = models.IntegerField(null=True, blank=True)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.card_last4:
            return f"{self.card_brand} ending in {self.card_last4}"
        return f"{self.payment_type} - {self.member.user.username}"


class PaymentWebhook(models.Model):
    """Log all payment gateway webhooks"""
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE, related_name='webhooks')
    
    event_type = models.CharField(max_length=100)
    event_id = models.CharField(max_length=255, unique=True)
    
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    
    received_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_webhooks'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['event_id']),
            models.Index(fields=['processed']),
        ]
    
    def __str__(self):
        return f"{self.gateway.gateway_type} - {self.event_type} - {self.received_at}"
