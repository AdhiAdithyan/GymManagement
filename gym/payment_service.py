"""
Payment Gateway Service
Handles Stripe and Razorpay payment processing
"""
import stripe
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from core.payment_models import (
    PaymentGateway,
    SubscriptionPayment,
    PaymentMethod
)
from core.models import MemberProfile, Subscription


class StripePaymentService:
    """Stripe payment gateway integration"""
    
    def __init__(self):
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
    
    @staticmethod
    def create_customer(member):
        """
        Create a Stripe customer for a member
        Returns: Stripe customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=member.user.email,
                name=member.user.get_full_name(),
                metadata={
                    'member_id': member.id,
                    'tenant_id': member.tenant.id if member.tenant else None
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    def create_payment_intent(amount, currency='inr', customer_id=None, metadata=None):
        """
        Create a payment intent for one-time payment
        amount: in smallest currency unit (paise for INR, cents for USD)
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to smallest unit
                currency=currency.lower(),
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            return intent
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    def create_subscription(customer_id, price_id, payment_method_id=None):
        """
        Create a recurring subscription
        price_id: Stripe price ID for the subscription plan
        """
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                default_payment_method=payment_method_id,
                expand=['latest_invoice.payment_intent']
            )
            return subscription
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    def attach_payment_method(payment_method_id, customer_id):
        """Attach a payment method to a customer"""
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            return payment_method
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    def set_default_payment_method(customer_id, payment_method_id):
        """Set default payment method for customer"""
        try:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method_id
                }
            )
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """Retrieve payment intent details"""
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    def cancel_subscription(subscription_id):
        """Cancel a subscription"""
        try:
            return stripe.Subscription.delete(subscription_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")


class RazorpayPaymentService:
    """Razorpay payment gateway integration (for Indian market)"""
    
    def __init__(self):
        try:
            import razorpay
            self.client = razorpay.Client(
                auth=(
                    getattr(settings, 'RAZORPAY_KEY_ID', ''),
                    getattr(settings, 'RAZORPAY_KEY_SECRET', '')
                )
            )
        except ImportError:
            raise Exception("Razorpay library not installed. Run: pip install razorpay")
    
    def create_order(self, amount, currency='INR', receipt=None, notes=None):
        """
        Create a Razorpay order
        amount: in smallest currency unit (paise)
        """
        try:
            order = self.client.order.create({
                'amount': int(amount * 100),
                'currency': currency,
                'receipt': receipt or f'receipt_{timezone.now().timestamp()}',
                'notes': notes or {}
            })
            return order
        except Exception as e:
            raise Exception(f"Razorpay error: {str(e)}")
    
    def verify_payment_signature(self, order_id, payment_id, signature):
        """Verify payment signature for security"""
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except Exception:
            return False
    
    def create_subscription(self, plan_id, total_count, customer_notify=1):
        """Create a recurring subscription"""
        try:
            subscription = self.client.subscription.create({
                'plan_id': plan_id,
                'total_count': total_count,
                'customer_notify': customer_notify
            })
            return subscription
        except Exception as e:
            raise Exception(f"Razorpay error: {str(e)}")


class PaymentManager:
    """
    Unified payment manager
    Handles payment operations across different gateways
    """
    
    @staticmethod
    def process_membership_payment(member, subscription, amount, payment_method='card', gateway_type='stripe'):
        """
        Process a membership payment
        Returns: SubscriptionPayment object
        """
        # Get payment gateway configuration
        gateway = PaymentGateway.objects.filter(
            tenant=member.tenant,
            gateway_type=gateway_type,
            is_active=True
        ).first()
        
        if not gateway:
            raise Exception(f"No active {gateway_type} gateway configured for this tenant")
        
        # Create payment record
        payment = SubscriptionPayment.objects.create(
            subscription=subscription,
            member=member,
            amount=amount,
            currency='INR',
            payment_method=payment_method,
            gateway=gateway,
            status='pending'
        )
        
        # Generate invoice number
        payment.generate_invoice_number()
        
        return payment
    
    @staticmethod
    def mark_payment_successful(payment, transaction_id, gateway_payment_id=None, gateway_response=None):
        """Mark a payment as successful"""
        payment.status = 'completed'
        payment.transaction_id = transaction_id
        payment.gateway_payment_id = gateway_payment_id or transaction_id
        payment.gateway_response = gateway_response or {}
        payment.save()
        
        # Update subscription status
        if payment.subscription:
            payment.subscription.status = 'active'
            payment.subscription.save()
        
        return payment
    
    @staticmethod
    def mark_payment_failed(payment, error_message):
        """Mark a payment as failed and schedule retry"""
        payment.status = 'failed'
        payment.gateway_response = {'error': error_message}
        payment.retry_count += 1
        
        # Schedule next retry (exponential backoff)
        if payment.retry_count < 3:
            retry_hours = 2 ** payment.retry_count  # 2, 4, 8 hours
            payment.next_retry_date = timezone.now() + timedelta(hours=retry_hours)
        
        payment.save()
        return payment
    
    @staticmethod
    def get_payment_history(member, limit=10):
        """Get payment history for a member"""
        return SubscriptionPayment.objects.filter(
            member=member
        ).order_by('-payment_date')[:limit]
    
    @staticmethod
    def get_pending_payments(tenant):
        """Get all pending payments for a tenant"""
        return SubscriptionPayment.objects.filter(
            member__tenant=tenant,
            status='pending'
        ).order_by('-created_at')
    
    @staticmethod
    def get_failed_payments_for_retry(tenant):
        """Get failed payments that are due for retry"""
        return SubscriptionPayment.objects.filter(
            member__tenant=tenant,
            status='failed',
            retry_count__lt=3,
            next_retry_date__lte=timezone.now()
        )


# Convenience functions
def create_stripe_payment(member, amount, description='Membership Payment'):
    """Quick function to create a Stripe payment"""
    service = StripePaymentService()
    
    # Get or create Stripe customer
    payment_method = PaymentMethod.objects.filter(
        member=member,
        gateway__gateway_type='stripe',
        is_active=True
    ).first()
    
    if not payment_method:
        # Create new customer
        customer_id = service.create_customer(member)
        # Save customer ID to member profile or payment method
    else:
        customer_id = payment_method.gateway_customer_id
    
    # Create payment intent
    intent = service.create_payment_intent(
        amount=amount,
        customer_id=customer_id,
        metadata={
            'member_id': member.id,
            'description': description
        }
    )
    
    return intent


def create_razorpay_payment(member, amount, description='Membership Payment'):
    """Quick function to create a Razorpay payment"""
    service = RazorpayPaymentService()
    
    order = service.create_order(
        amount=amount,
        notes={
            'member_id': member.id,
            'description': description
        }
    )
    
    return order
