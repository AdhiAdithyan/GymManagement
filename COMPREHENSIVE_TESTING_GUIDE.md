# 🧪 COMPREHENSIVE TESTING GUIDE - ALL ROLES

**Date:** January 24, 2026  
**Purpose:** Test all modules with each user role

---

## 🎯 Testing Strategy

We'll test the application with 4 user roles:
1. **Super Admin** - Platform owner
2. **Tenant Admin** - Gym owner
3. **Trainer** - Gym trainer
4. **Member** - Gym member

---

## 📋 Pre-Testing Setup

### 1. Start the Server
```bash
cd d:\Python\gym_management
python manage.py runserver
```

### 2. Create Test Users

Run this in Django shell:
```bash
python manage.py shell
```

```python
from core.models import Tenant, CustomUser, MemberProfile
from django.contrib.auth.hashers import make_password

# Create Tenant
tenant = Tenant.objects.create(
    name="Test Gym",
    subdomain="testgym",
    contact_email="admin@testgym.com",
    plan_type="premium"
)

# 1. Super Admin
super_admin = CustomUser.objects.create(
    username="superadmin",
    email="super@admin.com",
    password=make_password("admin123"),
    role="super_admin",
    is_staff=True,
    is_superuser=True
)

# 2. Tenant Admin
tenant_admin = CustomUser.objects.create(
    username="gymadmin",
    email="admin@testgym.com",
    password=make_password("admin123"),
    role="tenant_admin",
    tenant=tenant,
    is_staff=True
)

# 3. Trainer
trainer = CustomUser.objects.create(
    username="trainer1",
    email="trainer@testgym.com",
    password=make_password("trainer123"),
    role="trainer",
    tenant=tenant,
    first_name="John",
    last_name="Trainer"
)

# 4. Member
member_user = CustomUser.objects.create(
    username="member1",
    email="member@testgym.com",
    password=make_password("member123"),
    role="member",
    tenant=tenant,
    first_name="Jane",
    last_name="Member"
)

# Create Member Profile
member_profile = MemberProfile.objects.create(
    user=member_user,
    tenant=tenant,
    membership_type="monthly",
    age=25,
    registration_amount=1000,
    monthly_amount=500,
    allotted_slot="6:00 AM - 7:00 AM"
)

print("✅ Test users created successfully!")
print("Credentials:")
print("Super Admin: superadmin / admin123")
print("Tenant Admin: gymadmin / admin123")
print("Trainer: trainer1 / trainer123")
print("Member: member1 / member123")
```

---

## 🧪 TESTING CHECKLIST

### ROLE 1: SUPER ADMIN

**Login:** `superadmin / admin123`

#### Test Cases:
- [ ] 1. Login to system
- [ ] 2. Access Django Admin (`/admin/`)
- [ ] 3. View all tenants
- [ ] 4. Create new tenant
- [ ] 5. View all users across tenants
- [ ] 6. Access all models
- [ ] 7. View system-wide analytics
- [ ] 8. Logout

**Expected Results:**
- Full access to all features
- Can see all tenants
- Can manage all users
- No restrictions

---

### ROLE 2: TENANT ADMIN (Gym Owner)

**Login:** `gymadmin / admin123`

#### Test Cases:

**Dashboard & Overview:**
- [ ] 1. Login to system
- [ ] 2. View dashboard (`/`)
- [ ] 3. See member count
- [ ] 4. See revenue stats
- [ ] 5. See attendance overview

**Member Management:**
- [ ] 6. View member list (`/members/`)
- [ ] 7. Add new member (`/members/add/`)
- [ ] 8. Edit member (`/members/edit/{id}/`)
- [ ] 9. Delete member
- [ ] 10. Search members
- [ ] 11. Filter members

**Attendance:**
- [ ] 12. Mark attendance (`/attendance/mark/`)
- [ ] 13. Scan QR code (`/attendance/scan/`)
- [ ] 14. View attendance list

**Financial:**
- [ ] 15. View finance overview (`/finance/`)
- [ ] 16. Record payment
- [ ] 17. View payment history (`/admin/payments/`)
- [ ] 18. Configure payment gateway (`/admin/payment-settings/`)
- [ ] 19. View revenue stats

**Class Management:**
- [ ] 20. Create class schedule (`/admin/schedules/`)
- [ ] 21. View all bookings
- [ ] 22. Manage waitlist

**Reports:**
- [ ] 23. View reports (`/reports/`)
- [ ] 24. Export PDF (`/reports/export/`)

**Settings:**
- [ ] 25. Branding settings (`/branding/`)
- [ ] 26. WhatsApp configuration (`/whatsapp/send/`)

**Expected Results:**
- Can manage own gym only
- Cannot see other tenants
- Full admin features for own gym

---

### ROLE 3: TRAINER

**Login:** `trainer1 / trainer123`

#### Test Cases:

**Dashboard:**
- [ ] 1. Login to system
- [ ] 2. View trainer dashboard
- [ ] 3. See assigned members

**Attendance:**
- [ ] 4. Mark attendance (`/trainer/attendance/`)
- [ ] 5. View attendance history

**Content Management:**
- [ ] 6. Upload workout video (`/trainer/video/upload/`)
- [ ] 7. Create diet plan (`/trainer/diet/create/`)
- [ ] 8. View own content

**Leave Requests:**
- [ ] 9. View leave requests (`/leave/list/`)
- [ ] 10. Approve/reject leaves (`/leave/action/{id}/`)

**Classes:**
- [ ] 11. View assigned classes
- [ ] 12. See class bookings

**Expected Results:**
- Limited to trainer functions
- Cannot access financial data
- Cannot manage members
- Can view assigned content only

---

### ROLE 4: MEMBER

**Login:** `member1 / member123`

#### Test Cases:

**Dashboard:**
- [ ] 1. Login to system
- [ ] 2. View member dashboard (`/member/dashboard/`)
- [ ] 3. See membership info
- [ ] 4. See next payment date

**Attendance:**
- [ ] 5. View attendance history (`/member/attendance/`)
- [ ] 6. See attendance stats
- [ ] 7. View QR code (`/member/qr/`)

**Payments:**
- [ ] 8. View payment dashboard (`/payments/`)
- [ ] 9. Make payment (`/payments/create/`)
- [ ] 10. View payment history (`/payments/history/`)
- [ ] 11. View receipts

**Class Booking:**
- [ ] 12. View class calendar (`/classes/`)
- [ ] 13. Book a class
- [ ] 14. View my bookings (`/bookings/`)
- [ ] 15. Cancel booking

**Content:**
- [ ] 16. View workout videos (`/member/videos/`)
- [ ] 17. View diet plan (`/member/diet/`)

**Leave:**
- [ ] 18. Request leave (`/member/leave/`)
- [ ] 19. View leave status

**Expected Results:**
- Self-service features only
- Cannot access admin features
- Cannot see other members
- Can manage own bookings/payments

---

## 🐛 COMMON ISSUES TO CHECK

### 1. Permission Issues
```
Error: "You don't have permission"
Fix: Check role_required decorators
```

### 2. Template Not Found
```
Error: "TemplateDoesNotExist"
Fix: Check template paths
```

### 3. 404 Errors
```
Error: "Page not found"
Fix: Check URL patterns
```

### 4. Database Errors
```
Error: "DoesNotExist"
Fix: Check foreign key relationships
```

---

## 🔧 AUTOMATED TESTING SCRIPT

Save as `test_roles.py`:

```python
from django.test import TestCase, Client
from core.models import Tenant, CustomUser, MemberProfile

class RoleBasedAccessTest(TestCase):
    def setUp(self):
        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test Gym",
            subdomain="testgym",
            contact_email="test@gym.com"
        )
        
        # Create users
        self.super_admin = CustomUser.objects.create_user(
            username="super",
            password="test123",
            role="super_admin",
            is_superuser=True
        )
        
        self.tenant_admin = CustomUser.objects.create_user(
            username="admin",
            password="test123",
            role="tenant_admin",
            tenant=self.tenant
        )
        
        self.trainer = CustomUser.objects.create_user(
            username="trainer",
            password="test123",
            role="trainer",
            tenant=self.tenant
        )
        
        self.member_user = CustomUser.objects.create_user(
            username="member",
            password="test123",
            role="member",
            tenant=self.tenant
        )
        
        self.member = MemberProfile.objects.create(
            user=self.member_user,
            tenant=self.tenant,
            membership_type="monthly",
            age=25,
            registration_amount=1000,
            monthly_amount=500,
            allotted_slot="6:00 AM"
        )
        
        self.client = Client()
    
    def test_member_can_access_dashboard(self):
        self.client.login(username="member", password="test123")
        response = self.client.get('/member/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_member_cannot_access_admin(self):
        self.client.login(username="member", password="test123")
        response = self.client.get('/members/')
        self.assertNotEqual(response.status_code, 200)
    
    def test_admin_can_access_members(self):
        self.client.login(username="admin", password="test123")
        response = self.client.get('/members/')
        self.assertEqual(response.status_code, 200)
    
    def test_payment_dashboard_member_only(self):
        self.client.login(username="member", password="test123")
        response = self.client.get('/payments/')
        self.assertEqual(response.status_code, 200)

# Run with: python manage.py test
```

---

## 📊 TESTING RESULTS TEMPLATE

| Module | Super Admin | Tenant Admin | Trainer | Member | Status |
|--------|-------------|--------------|---------|--------|--------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | |
| Members | ✅ | ✅ | ❌ | ❌ | |
| Attendance | ✅ | ✅ | ✅ | View Only | |
| Payments | ✅ | ✅ | ❌ | ✅ | |
| Classes | ✅ | ✅ | ✅ | ✅ | |
| Reports | ✅ | ✅ | ❌ | ❌ | |
| Settings | ✅ | ✅ | ❌ | ❌ | |

---

## 🚀 QUICK TEST COMMANDS

```bash
# 1. Check system
python manage.py check

# 2. Run migrations
python manage.py migrate

# 3. Create superuser
python manage.py createsuperuser

# 4. Run tests
python manage.py test

# 5. Start server
python manage.py runserver
```

---

## 📝 ISSUE TRACKING

### Issue Template:
```
Issue #: 
Role: [Super Admin / Tenant Admin / Trainer / Member]
Module: [Dashboard / Payments / etc.]
URL: /path/to/page/
Error: Description of error
Expected: What should happen
Actual: What actually happened
Fix: Solution applied
Status: [Open / Fixed / Testing]
```

---

## ✅ TESTING COMPLETION CHECKLIST

- [ ] All test users created
- [ ] Super Admin tested (8 test cases)
- [ ] Tenant Admin tested (26 test cases)
- [ ] Trainer tested (12 test cases)
- [ ] Member tested (19 test cases)
- [ ] All issues documented
- [ ] All issues fixed
- [ ] Retested after fixes
- [ ] Documentation updated

---

**Total Test Cases:** 65  
**Estimated Time:** 2-3 hours  
**Priority:** High

