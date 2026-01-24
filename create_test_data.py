"""
Create Test Users and Sample Data
Run with: python manage.py shell < create_test_data.py
"""

from core.models import Tenant, CustomUser, MemberProfile, Subscription
from core.booking_models import ClassSchedule, BookingSettings
from core.payment_models import PaymentGateway
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta

print("🚀 Creating test users and sample data...")

# 1. Create or get tenant
tenant, created = Tenant.objects.get_or_create(
    subdomain="testgym",
    defaults={
        'name': "Test Gym",
        'contact_email': "admin@testgym.com",
        'plan_type': "premium"
    }
)
print(f"✅ Tenant: {tenant.name} ({'created' if created else 'exists'})")

# 2. Create Super Admin
super_admin, created = CustomUser.objects.get_or_create(
    username="superadmin",
    defaults={
        'email': "super@admin.com",
        'password': make_password("admin123"),
        'role': "super_admin",
        'is_staff': True,
        'is_superuser': True,
        'first_name': "Super",
        'last_name': "Admin"
    }
)
if created:
    print("✅ Super Admin created: superadmin / admin123")
else:
    print("ℹ️  Super Admin exists: superadmin")

# 3. Create Tenant Admin
tenant_admin, created = CustomUser.objects.get_or_create(
    username="gymadmin",
    defaults={
        'email': "admin@testgym.com",
        'password': make_password("admin123"),
        'role': "tenant_admin",
        'tenant': tenant,
        'is_staff': True,
        'first_name': "Gym",
        'last_name': "Admin"
    }
)
if created:
    print("✅ Tenant Admin created: gymadmin / admin123")
else:
    print("ℹ️  Tenant Admin exists: gymadmin")

# 4. Create Trainer
trainer, created = CustomUser.objects.get_or_create(
    username="trainer1",
    defaults={
        'email': "trainer@testgym.com",
        'password': make_password("trainer123"),
        'role': "trainer",
        'tenant': tenant,
        'first_name': "John",
        'last_name': "Trainer"
    }
)
if created:
    print("✅ Trainer created: trainer1 / trainer123")
else:
    print("ℹ️  Trainer exists: trainer1")

# 5. Create Member User
member_user, created = CustomUser.objects.get_or_create(
    username="member1",
    defaults={
        'email': "member@testgym.com",
        'password': make_password("member123"),
        'role': "member",
        'tenant': tenant,
        'first_name': "Jane",
        'last_name': "Member"
    }
)

# 6. Create Member Profile
if created:
    member_profile = MemberProfile.objects.create(
        user=member_user,
        tenant=tenant,
        membership_type="monthly",
        age=25,
        registration_amount=1000,
        monthly_amount=500,
        allotted_slot="6:00 AM - 7:00 AM",
        phone_number="+919876543210",
        next_payment_date=timezone.now().date() + timedelta(days=30)
    )
    print("✅ Member created: member1 / member123")
    
    # Create subscription
    Subscription.objects.create(
        member=member_profile,
        plan='monthly',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=30),
        status='active'
    )
    print("✅ Member subscription created")
else:
    print("ℹ️  Member exists: member1")
    member_profile = member_user.member_profile

# 7. Create additional members for testing
for i in range(2, 6):
    user, created = CustomUser.objects.get_or_create(
        username=f"member{i}",
        defaults={
            'email': f"member{i}@testgym.com",
            'password': make_password("member123"),
            'role': "member",
            'tenant': tenant,
            'first_name': f"Member",
            'last_name': f"{i}"
        }
    )
    
    if created:
        MemberProfile.objects.create(
            user=user,
            tenant=tenant,
            membership_type=["monthly", "quarterly", "yearly"][i % 3],
            age=20 + i * 5,
            registration_amount=1000,
            monthly_amount=500,
            allotted_slot=["6:00 AM - 7:00 AM", "7:00 AM - 8:00 AM", "6:00 PM - 7:00 PM"][i % 3],
            phone_number=f"+9198765432{10+i}",
            next_payment_date=timezone.now().date() + timedelta(days=30)
        )
        print(f"✅ Additional member created: member{i} / member123")

# 8. Create Class Schedules
class_schedules = [
    {
        'class_name': 'Yoga',
        'class_type': 'yoga',
        'day_of_week': 1,  # Monday
        'start_time': '06:00',
        'end_time': '07:00',
        'capacity': 15,
        'description': 'Morning yoga session for flexibility and relaxation'
    },
    {
        'class_name': 'HIIT Training',
        'class_type': 'hiit',
        'day_of_week': 2,  # Tuesday
        'start_time': '18:00',
        'end_time': '19:00',
        'capacity': 20,
        'description': 'High-intensity interval training for fat loss'
    },
    {
        'class_name': 'Strength Training',
        'class_type': 'strength',
        'day_of_week': 3,  # Wednesday
        'start_time': '07:00',
        'end_time': '08:00',
        'capacity': 12,
        'description': 'Build muscle and strength'
    },
    {
        'class_name': 'Zumba',
        'class_type': 'cardio',
        'day_of_week': 4,  # Thursday
        'start_time': '18:30',
        'end_time': '19:30',
        'capacity': 25,
        'description': 'Fun cardio dance workout'
    },
]

for schedule_data in class_schedules:
    schedule, created = ClassSchedule.objects.get_or_create(
        tenant=tenant,
        class_name=schedule_data['class_name'],
        day_of_week=schedule_data['day_of_week'],
        defaults={
            **schedule_data,
            'instructor': trainer,
            'is_active': True
        }
    )
    if created:
        print(f"✅ Class schedule created: {schedule_data['class_name']}")

# 9. Create Booking Settings
booking_settings, created = BookingSettings.objects.get_or_create(
    tenant=tenant,
    defaults={
        'allow_waitlist': True,
        'max_advance_booking_days': 7,
        'cancellation_hours': 2,
        'auto_cancel_no_show': True
    }
)
if created:
    print("✅ Booking settings created")

# 10. Create Payment Gateway (Test Mode)
gateway, created = PaymentGateway.objects.get_or_create(
    tenant=tenant,
    gateway_type='stripe',
    defaults={
        'api_key': 'pk_test_sample_key',
        'api_secret': 'sk_test_sample_secret',
        'is_test_mode': True,
        'is_active': True
    }
)
if created:
    print("✅ Payment gateway created (test mode)")

print("\n" + "="*60)
print("🎉 TEST DATA CREATION COMPLETE!")
print("="*60)
print("\n📝 LOGIN CREDENTIALS:\n")
print("1. Super Admin:")
print("   Username: superadmin")
print("   Password: admin123")
print("   URL: http://127.0.0.1:8000/admin/\n")

print("2. Tenant Admin (Gym Owner):")
print("   Username: gymadmin")
print("   Password: admin123")
print("   URL: http://127.0.0.1:8000/\n")

print("3. Trainer:")
print("   Username: trainer1")
print("   Password: trainer123")
print("   URL: http://127.0.0.1:8000/\n")

print("4. Member:")
print("   Username: member1")
print("   Password: member123")
print("   URL: http://127.0.0.1:8000/member/dashboard/\n")

print("Additional Members: member2-member5 / member123\n")

print("="*60)
print("✅ You can now start testing!")
print("Run: python manage.py runserver")
print("="*60)
