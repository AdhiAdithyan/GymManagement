"""
Payment Views
Handle payment-related user interactions
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import models
import json
import stripe

from core.models import MemberProfile, Subscription
from core.payment_models import (
    PaymentGateway,
    SubscriptionPayment,
    PaymentMethod,
    PaymentWebhook
)
from .payment_service import (
    StripePaymentService,
    PaymentManager,
    create_stripe_payment
)
from core.decorators import role_required


@login_required
@role_required(['member'])
def payment_dashboard(request):
    """Member payment dashboard"""
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum
    
    member = request.user.member_profile
    
    # Get payment history
    payments = SubscriptionPayment.objects.filter(
        member=member
    ).order_by('-payment_date')[:10]
    
    # Get active subscription
    active_subscription = Subscription.objects.filter(
        member=member,
        status='active'
    ).first()
    
    # Get saved payment methods
    payment_methods = PaymentMethod.objects.filter(
        member=member,
        is_active=True
    )
    
    # Calculate next payment
    next_payment_amount = member.monthly_amount if member.monthly_amount else 0
    next_payment_date = member.next_payment_date
    
    # Calculate total paid this year
    current_year = timezone.now().year
    total_paid = SubscriptionPayment.objects.filter(
        member=member,
        status='completed',
        payment_date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    payments_count = SubscriptionPayment.objects.filter(
        member=member,
        status='completed',
        payment_date__year=current_year
    ).count()
    
    # Date helpers
    today = timezone.now().date()
    seven_days_from_now = today + timedelta(days=7)
    
    context = {
        'member': member,
        'payments': payments,
        'active_subscription': active_subscription,
        'payment_methods': payment_methods,
        'next_payment_amount': next_payment_amount,
        'next_payment_date': next_payment_date,
        'total_paid': total_paid,
        'payments_count': payments_count,
        'today': today,
        'seven_days_from_now': seven_days_from_now,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    
    return render(request, 'gym/payment_dashboard.html', context)


@login_required
@role_required(['member'])
def create_payment(request):
    """Create a new payment"""
    member = request.user.member_profile
    
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        payment_type = request.POST.get('payment_type', 'monthly')
        gateway_type = request.POST.get('gateway', 'stripe')
        
        if amount <= 0:
            messages.error(request, 'Invalid payment amount')
            return redirect('payment_dashboard')
        
        # Get active subscription
        subscription = Subscription.objects.filter(
            member=member,
            status='active'
        ).first()
        
        if not subscription:
            messages.error(request, 'No active subscription found')
            return redirect('payment_dashboard')
        
        try:
            if gateway_type == 'stripe':
                # Create Stripe payment intent
                intent = create_stripe_payment(
                    member=member,
                    amount=amount,
                    description=f'{payment_type.title()} Payment'
                )
                
                # Create payment record
                payment = PaymentManager.process_membership_payment(
                    member=member,
                    subscription=subscription,
                    amount=amount,
                    payment_method='card',
                    gateway_type='stripe'
                )
                
                payment.gateway_payment_id = intent.id
                payment.save()
                
                # Return client secret for frontend
                return JsonResponse({
                    'clientSecret': intent.client_secret,
                    'payment_id': payment.id
                })
            
            elif gateway_type == 'razorpay':
                # TODO: Implement Razorpay payment
                messages.info(request, 'Razorpay integration coming soon')
                return redirect('payment_dashboard')
            
        except Exception as e:
            messages.error(request, f'Payment error: {str(e)}')
            return redirect('payment_dashboard')
    
    # GET request - show payment form
    context = {
        'member': member,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'gym/create_payment.html', context)


@login_required
@role_required(['member'])
def payment_success(request, payment_id):
    """Payment success page"""
    payment = get_object_or_404(SubscriptionPayment, id=payment_id, member=request.user.member_profile)
    
    context = {
        'payment': payment,
    }
    return render(request, 'gym/payment_success.html', context)


@login_required
@role_required(['member'])
def payment_history(request):
    """View payment history"""
    from django.db.models import Sum, Count, Q
    from django.core.paginator import Paginator
    
    member = request.user.member_profile
    
    # Base queryset
    payments = SubscriptionPayment.objects.filter(
        member=member
    )
    
    # Apply filters
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    status = request.GET.get('status')
    method = request.GET.get('method')
    
    if from_date:
        payments = payments.filter(payment_date__gte=from_date)
    if to_date:
        payments = payments.filter(payment_date__lte=to_date)
    if status:
        payments = payments.filter(status=status)
    if method:
        payments = payments.filter(payment_method=method)
    
    # Order by date
    payments = payments.order_by('-payment_date')
    
    # Calculate statistics
    stats = SubscriptionPayment.objects.filter(member=member).aggregate(
        total_amount=Sum('amount', filter=Q(status='completed')),
        total_payments=Count('id'),
        completed_payments=Count('id', filter=Q(status='completed')),
        pending_payments=Count('id', filter=Q(status='pending'))
    )
    
    # Pagination
    paginator = Paginator(payments, 20)  # 20 payments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'payments': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_amount': stats['total_amount'] or 0,
        'total_payments': stats['total_payments'],
        'completed_payments': stats['completed_payments'],
        'pending_payments': stats['pending_payments'],
    }
    return render(request, 'gym/payment_history.html', context)


@login_required
@role_required(['tenant_admin', 'super_admin'])
def admin_payment_overview(request):
    """Admin view of all payments"""
    tenant = request.user.tenant
    
    # Get all payments for this tenant
    payments = SubscriptionPayment.objects.filter(
        member__tenant=tenant
    ).order_by('-payment_date')[:50]
    
    # Get payment statistics
    from django.db.models import Sum, Count
    stats = SubscriptionPayment.objects.filter(
        member__tenant=tenant
    ).aggregate(
        total_revenue=Sum('amount', filter=models.Q(status='completed')),
        pending_count=Count('id', filter=models.Q(status='pending')),
        failed_count=Count('id', filter=models.Q(status='failed')),
        completed_count=Count('id', filter=models.Q(status='completed'))
    )
    
    # Get failed payments for retry
    failed_payments = PaymentManager.get_failed_payments_for_retry(tenant)
    
    context = {
        'payments': payments,
        'stats': stats,
        'failed_payments': failed_payments,
    }
    return render(request, 'gym/admin_payment_overview.html', context)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhooks
    This endpoint receives payment events from Stripe
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)
    
    # Log webhook
    gateway = PaymentGateway.objects.filter(gateway_type='stripe').first()
    if gateway:
        PaymentWebhook.objects.create(
            gateway=gateway,
            event_type=event['type'],
            event_id=event['id'],
            payload=event
        )
    
    # Handle different event types
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # Find and update payment
        payment = SubscriptionPayment.objects.filter(
            gateway_payment_id=payment_intent['id']
        ).first()
        
        if payment:
            PaymentManager.mark_payment_successful(
                payment=payment,
                transaction_id=payment_intent['id'],
                gateway_response=payment_intent
            )
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        
        # Find and update payment
        payment = SubscriptionPayment.objects.filter(
            gateway_payment_id=payment_intent['id']
        ).first()
        
        if payment:
            error_message = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
            PaymentManager.mark_payment_failed(
                payment=payment,
                error_message=error_message
            )
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Handle subscription cancellation
        # TODO: Update subscription status in database
        pass
    
    return HttpResponse(status=200)


@login_required
@role_required(['tenant_admin', 'super_admin'])
def payment_gateway_settings(request):
    """Configure payment gateway settings"""
    tenant = request.user.tenant
    
    if request.method == 'POST':
        gateway_type = request.POST.get('gateway_type')
        api_key = request.POST.get('api_key')
        api_secret = request.POST.get('api_secret')
        webhook_secret = request.POST.get('webhook_secret', '')
        is_test_mode = request.POST.get('is_test_mode') == 'on'
        
        # Create or update gateway
        gateway, created = PaymentGateway.objects.update_or_create(
            tenant=tenant,
            gateway_type=gateway_type,
            defaults={
                'api_key': api_key,
                'api_secret': api_secret,
                'webhook_secret': webhook_secret,
                'is_test_mode': is_test_mode,
                'is_active': True
            }
        )
        
        messages.success(request, f'{gateway_type.title()} gateway configured successfully')
        return redirect('payment_gateway_settings')
    
    # GET request
    gateways = PaymentGateway.objects.filter(tenant=tenant)
    
    context = {
        'gateways': gateways,
    }
    return render(request, 'gym/payment_gateway_settings.html', context)
