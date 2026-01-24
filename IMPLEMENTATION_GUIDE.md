# Modernization Implementation Guide

**Date:** January 24, 2026  
**Status:** Ready for Implementation

## Overview

This guide provides step-by-step instructions for implementing the modernization enhancements validated against industry standards (Mindbody, Glofox, Zenplanner, etc.).

---

## Phase 1: Critical Business Features (Weeks 1-4)

### 1.1 Payment Gateway Integration ⭐⭐⭐⭐⭐

#### Step 1: Install Dependencies
```bash
pip install stripe>=7.0.0 razorpay>=1.4.0 cryptography>=41.0.0
```

#### Step 2: Register New Models
Add to `core/models.py`:
```python
from .payment_models import (
    PaymentGateway,
    SubscriptionPayment,
    PaymentMethod,
    PaymentWebhook
)
```

#### Step 3: Create Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 4: Configure Environment Variables
Add to `.env`:
```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

#### Step 5: Create Payment Service
Create `gym/payment_service.py`:
```python
import stripe
from django.conf import settings
from core.payment_models import SubscriptionPayment, PaymentGateway

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    @staticmethod
    def create_stripe_customer(member):
        """Create Stripe customer for member"""
        customer = stripe.Customer.create(
            email=member.user.email,
            name=member.user.get_full_name(),
            metadata={'member_id': member.id}
        )
        return customer.id
    
    @staticmethod
    def create_subscription(member, plan_id, payment_method_id):
        """Create recurring subscription"""
        subscription = stripe.Subscription.create(
            customer=member.stripe_customer_id,
            items=[{'price': plan_id}],
            default_payment_method=payment_method_id,
        )
        return subscription
    
    @staticmethod
    def handle_failed_payment(payment_id):
        """Retry failed payment"""
        payment = SubscriptionPayment.objects.get(id=payment_id)
        # Implement retry logic
        pass
```

#### Step 6: Create Webhook Handler
Create `gym/webhooks.py`:
```python
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import stripe

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    
    # Handle different event types
    if event['type'] == 'payment_intent.succeeded':
        # Update payment status
        pass
    elif event['type'] == 'payment_intent.payment_failed':
        # Handle failed payment
        pass
    
    return HttpResponse(status=200)
```

#### Step 7: Add URL Routes
Add to `gym/urls.py`:
```python
path('webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
path('payments/create/', create_payment, name='create_payment'),
path('payments/history/', payment_history, name='payment_history'),
```

---

### 1.2 Self-Service Booking System ⭐⭐⭐⭐⭐

#### Step 1: Install Dependencies
```bash
pip install django-scheduler>=0.10.0
```

#### Step 2: Register Booking Models
Add to `core/models.py`:
```python
from .booking_models import (
    ClassSchedule,
    ClassBooking,
    PersonalTrainingSession,
    BookingSettings
)
```

#### Step 3: Create Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 4: Create Booking Service
Create `gym/booking_service.py`:
```python
from django.utils import timezone
from datetime import datetime, timedelta
from core.booking_models import ClassSchedule, ClassBooking

class BookingService:
    @staticmethod
    def get_available_classes(member, date):
        """Get available classes for a specific date"""
        day_of_week = date.weekday()
        schedules = ClassSchedule.objects.filter(
            tenant=member.tenant,
            day_of_week=day_of_week,
            is_active=True
        )
        
        available = []
        for schedule in schedules:
            # Check capacity
            confirmed_count = ClassBooking.objects.filter(
                class_schedule=schedule,
                booking_date=date,
                status='confirmed'
            ).count()
            
            if confirmed_count < schedule.capacity:
                available.append({
                    'schedule': schedule,
                    'spots_left': schedule.capacity - confirmed_count,
                    'can_book': True
                })
            else:
                # Check waitlist
                waitlist_count = ClassBooking.objects.filter(
                    class_schedule=schedule,
                    booking_date=date,
                    status='waitlist'
                ).count()
                
                if waitlist_count < schedule.waitlist_capacity:
                    available.append({
                        'schedule': schedule,
                        'spots_left': 0,
                        'can_book': True,
                        'waitlist': True
                    })
        
        return available
    
    @staticmethod
    def book_class(member, schedule, date):
        """Book a class for member"""
        # Check if already booked
        existing = ClassBooking.objects.filter(
            member=member,
            class_schedule=schedule,
            booking_date=date
        ).first()
        
        if existing:
            raise ValueError("Already booked for this class")
        
        # Check capacity
        confirmed_count = ClassBooking.objects.filter(
            class_schedule=schedule,
            booking_date=date,
            status='confirmed'
        ).count()
        
        if confirmed_count < schedule.capacity:
            # Book confirmed
            booking = ClassBooking.objects.create(
                class_schedule=schedule,
                member=member,
                booking_date=date,
                status='confirmed'
            )
        else:
            # Add to waitlist
            waitlist_count = ClassBooking.objects.filter(
                class_schedule=schedule,
                booking_date=date,
                status='waitlist'
            ).count()
            
            if waitlist_count >= schedule.waitlist_capacity:
                raise ValueError("Waitlist is full")
            
            booking = ClassBooking.objects.create(
                class_schedule=schedule,
                member=member,
                booking_date=date,
                status='waitlist',
                waitlist_position=waitlist_count + 1
            )
        
        return booking
```

#### Step 5: Create Calendar View
Create `templates/gym/class_calendar.html`:
```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <title>Class Schedule</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.css">
</head>
<body>
    <div id="calendar"></div>
    
    <script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var calendarEl = document.getElementById('calendar');
            var calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'timeGridWeek',
                events: '/api/classes/schedule/',
                eventClick: function(info) {
                    // Show booking modal
                    showBookingModal(info.event);
                }
            });
            calendar.render();
        });
    </script>
</body>
</html>
```

---

### 1.3 HTMX Integration for Dynamic UX ⭐⭐⭐⭐

#### Step 1: Install HTMX
```bash
pip install django-htmx>=1.17.0
```

#### Step 2: Add Middleware
Add to `settings.py`:
```python
MIDDLEWARE = [
    # ... existing middleware
    'django_htmx.middleware.HtmxMiddleware',
]
```

#### Step 3: Add HTMX to Base Template
Update `templates/base.html`:
```html
<head>
    <!-- Existing head content -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
```

#### Step 4: Convert Attendance Marking to HTMX
Update `templates/gym/mark_attendance.html`:
```html
<div id="attendance-list">
    {% for member in members %}
    <div class="member-card">
        <img src="{{ member.image.url }}" alt="{{ member.user.username }}">
        <h3>{{ member.user.get_full_name }}</h3>
        
        <button 
            hx-post="{% url 'mark_attendance_ajax' member.id %}"
            hx-target="#attendance-list"
            hx-swap="outerHTML"
            class="btn-primary">
            Mark Present
        </button>
    </div>
    {% endfor %}
</div>
```

Create HTMX view in `gym/views.py`:
```python
from django_htmx.http import HttpResponseClientRefresh

@login_required
def mark_attendance_ajax(request, member_id):
    if request.htmx:
        member = get_object_or_404(MemberProfile, id=member_id)
        Attendance.objects.create(
            tenant=request.user.tenant,
            member=member,
            date=timezone.now().date()
        )
        
        # Return updated list
        members = MemberProfile.objects.filter(tenant=request.user.tenant)
        return render(request, 'gym/partials/attendance_list.html', {
            'members': members
        })
    
    return HttpResponse(status=400)
```

---

## Phase 2: Member Engagement (Weeks 5-8)

### 2.1 Workout Logging & Gamification ⭐⭐⭐⭐

#### Step 1: Register Gamification Models
Add to `core/models.py`:
```python
from .gamification_models import (
    Exercise,
    WorkoutLog,
    PersonalBest,
    Achievement,
    MemberEngagementScore,
    Leaderboard,
    Challenge,
    ChallengeParticipation
)
```

#### Step 2: Create Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 3: Seed Exercise Database
Create `core/management/commands/seed_exercises.py`:
```python
from django.core.management.base import BaseCommand
from core.gamification_models import Exercise

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        exercises = [
            {
                'name': 'Bench Press',
                'category': 'strength',
                'measurement_type': 'weight',
                'muscle_groups': ['chest', 'triceps', 'shoulders']
            },
            {
                'name': 'Squat',
                'category': 'strength',
                'measurement_type': 'weight',
                'muscle_groups': ['quads', 'glutes', 'hamstrings']
            },
            # Add more exercises
        ]
        
        for ex in exercises:
            Exercise.objects.get_or_create(**ex)
        
        self.stdout.write('Exercises seeded successfully')
```

Run:
```bash
python manage.py seed_exercises
```

#### Step 4: Create Workout Logging View
Create `templates/gym/log_workout.html`:
```html
<form method="post" hx-post="{% url 'log_workout' %}" hx-target="#workout-history">
    {% csrf_token %}
    
    <select name="exercise" required>
        {% for exercise in exercises %}
        <option value="{{ exercise.id }}">{{ exercise.name }}</option>
        {% endfor %}
    </select>
    
    <input type="number" name="weight" placeholder="Weight (kg)" step="0.1">
    <input type="number" name="sets" placeholder="Sets">
    <input type="number" name="reps" placeholder="Reps">
    
    <button type="submit">Log Workout</button>
</form>

<div id="workout-history">
    <!-- Workout history will be loaded here -->
</div>
```

---

### 2.2 AI Workout Plan Generator ⭐⭐⭐

#### Step 1: Install Gemini AI
```bash
pip install google-generativeai>=0.3.0
```

#### Step 2: Configure API Key
Add to `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

#### Step 3: Create AI Service
Create `gym/ai_service.py`:
```python
import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

class AIWorkoutService:
    @staticmethod
    def generate_workout_plan(member):
        """Generate personalized workout plan using Gemini AI"""
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Create a personalized 4-week workout plan for:
        - Age: {member.age}
        - Membership Type: {member.membership_type}
        - Current Fitness Level: Intermediate
        
        Include:
        1. Weekly schedule (3-5 days)
        2. Specific exercises with sets/reps
        3. Progressive overload strategy
        4. Rest days
        
        Format as structured JSON.
        """
        
        response = model.generate_content(prompt)
        return response.text
    
    @staticmethod
    def generate_diet_plan(member, goal='maintenance'):
        """Generate personalized diet plan"""
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Create a personalized diet plan for:
        - Age: {member.age}
        - Goal: {goal}
        - Dietary Restrictions: None
        
        Include:
        1. Daily calorie target
        2. Macronutrient breakdown
        3. Sample meal plan (3 meals + 2 snacks)
        4. Hydration recommendations
        
        Format as structured text.
        """
        
        response = model.generate_content(prompt)
        return response.text
```

---

## Phase 3: Analytics & Monitoring (Weeks 9-12)

### 3.1 Engagement Scoring & Churn Prediction

#### Step 1: Create Analytics Service
Create `gym/analytics_service.py`:
```python
from datetime import datetime, timedelta
from django.utils import timezone
from core.gamification_models import MemberEngagementScore
from core.models import Attendance, Payment

class AnalyticsService:
    @staticmethod
    def calculate_engagement_score(member):
        """Calculate comprehensive engagement score"""
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Attendance metrics
        total_attendance = Attendance.objects.filter(
            member=member,
            date__gte=thirty_days_ago
        ).count()
        
        attendance_rate = (total_attendance / 30) * 100
        
        # Last visit
        last_attendance = Attendance.objects.filter(
            member=member
        ).order_by('-date').first()
        
        if last_attendance:
            last_visit_days = (now.date() - last_attendance.date).days
        else:
            last_visit_days = 999
        
        # Payment status
        last_payment = Payment.objects.filter(
            member=member
        ).order_by('-date').first()
        
        if member.next_payment_date:
            days_until_due = (member.next_payment_date - now.date()).days
            if days_until_due < 0:
                payment_status = 'overdue'
            elif days_until_due < 7:
                payment_status = 'due'
            else:
                payment_status = 'current'
        else:
            payment_status = 'current'
        
        # Calculate scores
        attendance_score = min(attendance_rate * 3.33, 100)  # Scale to 100
        payment_score = 100 if payment_status == 'current' else 50
        
        # Overall score (weighted average)
        overall_score = (
            attendance_score * 0.6 +
            payment_score * 0.4
        )
        
        # Churn risk calculation
        if last_visit_days > 14 or payment_status == 'overdue':
            churn_risk = 'high'
            churn_probability = 75
        elif last_visit_days > 7 or payment_status == 'due':
            churn_risk = 'medium'
            churn_probability = 40
        else:
            churn_risk = 'low'
            churn_probability = 10
        
        # Create or update engagement score
        score, created = MemberEngagementScore.objects.update_or_create(
            member=member,
            defaults={
                'overall_score': overall_score,
                'attendance_score': attendance_score,
                'payment_score': payment_score,
                'attendance_rate_30d': attendance_rate,
                'last_visit_days_ago': last_visit_days,
                'payment_status': payment_status,
                'days_until_payment_due': days_until_due if member.next_payment_date else None,
                'churn_risk': churn_risk,
                'churn_probability': churn_probability,
                'calculated_at': now
            }
        )
        
        return score
```

---

## Database Migration Strategy

### Step 1: Create All Migrations
```bash
python manage.py makemigrations core
python manage.py makemigrations gym
```

### Step 2: Review Migrations
```bash
python manage.py showmigrations
```

### Step 3: Apply Migrations
```bash
python manage.py migrate
```

### Step 4: Verify Database
```bash
python manage.py dbshell
.tables  # SQLite
\dt      # PostgreSQL
```

---

## Testing Strategy

### Unit Tests
Create `tests/test_payment_service.py`:
```python
import pytest
from gym.payment_service import PaymentService

@pytest.mark.django_db
def test_create_stripe_customer():
    # Test implementation
    pass
```

### Integration Tests
```bash
pytest tests/ -v --cov=gym --cov=core
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All migrations created and tested locally
- [ ] Environment variables configured
- [ ] Payment gateway test mode verified
- [ ] Webhook endpoints tested
- [ ] HTMX functionality tested
- [ ] AI service tested with API key

### Production Deployment
- [ ] Update requirements.txt on server
- [ ] Run `pip install -r requirements.txt`
- [ ] Run migrations: `python manage.py migrate`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Restart application server
- [ ] Configure webhook URLs in Stripe/Razorpay dashboard
- [ ] Test payment flow end-to-end
- [ ] Monitor error logs

---

## Monitoring & Maintenance

### Daily
- Check payment webhook logs
- Monitor failed payments
- Review churn risk alerts

### Weekly
- Calculate engagement scores for all members
- Review booking patterns
- Update leaderboards

### Monthly
- Generate analytics reports
- Review AI-generated content quality
- Optimize database queries

---

## Support & Resources

### Documentation
- Stripe API: https://stripe.com/docs/api
- Razorpay API: https://razorpay.com/docs/api/
- HTMX: https://htmx.org/docs/
- Gemini AI: https://ai.google.dev/docs

### Community
- Django Forum: https://forum.djangoproject.com/
- Stack Overflow: Tag with `django`, `stripe`, `htmx`

---

**Implementation Status:** Ready to Begin  
**Estimated Timeline:** 12 weeks for full implementation  
**Priority:** Start with Phase 1 (Payment + Booking)
