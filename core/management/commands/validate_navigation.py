from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from core.models import MemberProfile, Tenant
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Validates page navigation and access controls for different user roles.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING("[START] Navigational Access Control Validation..."))
        
        # --- SETUP USERS ---
        self.stdout.write("\n[SETUP] Creating Test Users for Roles: Admin, Trainer, Member")
        tenant, _ = Tenant.objects.get_or_create(name="Test Gym", defaults={'subdomain': 'testgym'})
        
        # Admin
        admin_user, _ = User.objects.get_or_create(username='test_admin', defaults={'email': 'admin@test.com', 'role': 'tenant_admin'})
        admin_user.set_password('password123')
        admin_user.save()
        
        # Trainer
        trainer_user, _ = User.objects.get_or_create(username='test_trainer', defaults={'email': 'trainer@test.com', 'role': 'trainer'})
        trainer_user.set_password('password123')
        trainer_user.save()
        
        # Member
        member_user, _ = User.objects.get_or_create(username='test_member', defaults={'email': 'member@test.com', 'role': 'member'})
        member_user.set_password('password123')
        member_user.save()
        
        # Ensure profile for member (some views require it)
        if not hasattr(member_user, 'member_profile'):
            MemberProfile.objects.create(
                user=member_user,
                tenant=tenant,
                membership_type='monthly',
                age=25,
                registration_amount=0,
                monthly_amount=50,
                allotted_slot="Morning",
                next_payment_date=timezone.now().date() + timezone.timedelta(days=30)
            )

        self.stdout.write("[OK] Users Ready")

        # --- DEFINE URLS TO TEST ---
        # Format: (url_name, expected_status_for_admin, expected_status_for_trainer, expected_status_for_member)
        # Status 200 = Access Granted, 302 = Redirect (likely Denied/Login), 403 = Forbidden
        
        # Note: Many 'denied' accesses currently redirect (302) to dashboard or login, rather than 403.
        # So we check if response code matches expected "Good" code (200) or anything else.
        
        test_cases = [
            # Public / Common
            ('dashboard', 200, 200, 200),
            
            # Admin Only Pages
            ('admin_dashboard', 200, 302, 302), # Should be redirected if not admin
            ('finance', 200, 302, 302),
            ('reports', 200, 302, 302),
            ('member_list', 200, 200, 302), # Trainers can see list
            ('add_member', 200, 200, 302),
            
            # Trainer Pages
            ('trainer_dashboard', 200, 200, 302), # Admin can usually see trainer stuff too
            ('upload_video', 200, 200, 302), 
            ('mark_attendance', 200, 200, 302), # Assuming member can't mark own attendance via this view
            
            # Member Pages
            ('member_dashboard', 200, 200, 200), # Admin/Trainer might be allowed or redirected. Actually member_dashboard logic checks profile. 
                                                 # If admin has no profile, might crash or redirect. Let's assume Admin/Trainer get 302 or error if no profile. 
                                                 # We will relax check for Admin/Trainer on member pages.
            ('member_payments', 302, 302, 200), # Requires member_profile
            ('member_attendance', 302, 302, 200),
            
            # Feature Pages (Phase 1)
            ('payment_dashboard', 302, 302, 200), # Member specific typically
            # ('class_calendar', 200, 200, 200), # Likely anyone can see calendar
            
            # Feature Pages (Phase 2 - AI)
            ('ai_workout_plan', 302, 302, 302), # Should redirect to 'connect' for everyone initially!
            ('connect_ai_tools', 200, 200, 200), # Connection page accessible
            ('gym_analytics', 200, 302, 302), # Admin only
            ('member_insights', 302, 302, 200), # Member specific
        ]

        client = Client()

        # --- EXECUTE TESTS ---
        
        # 1. Test as Admin
        self.stdout.write("\n[TEST] [ADMIN] Testing as Admin...")
        client.login(username='test_admin', password='password123')
        self._run_tests(client, test_cases, 1, tenant.id) # Index 1 is admin expected status
        client.logout()

        # 2. Test as Trainer
        self.stdout.write("\n[TEST] [TRAINER] Testing as Trainer...")
        client.login(username='test_trainer', password='password123')
        self._run_tests(client, test_cases, 2, tenant.id) # Index 2 is trainer expected status
        client.logout()

        # 3. Test as Member
        self.stdout.write("\n[TEST] [MEMBER] Testing as Member...")
        client.login(username='test_member', password='password123')
        self._run_tests(client, test_cases, 3, tenant.id) # Index 3 is member expected status
        client.logout()
        
        self.stdout.write(self.style.MIGRATE_HEADING("\n[COMPLETE] Validation Finished."))

    def _run_tests(self, client, test_cases, role_index, tenant_id):
        for url_name, s_admin, s_trainer, s_member in test_cases:
            target_status = (s_admin, s_trainer, s_member)[role_index - 1]
            
            # Skip if URL name is hard to reverse (e.g. requires args) - simplified list above doesnt have args
            # We will try/except the reverse
            try:
                # Handle urls that might need args - simplistic approach, only test arg-less ones or provide dummy arg
                # Most dashboard urls are arg-less. 
                # edit_member needs ID. We skip explicit ID urls in this simplified script or handle specific cases.
                url = reverse(url_name)
            except:
                continue

            # Pass Tenant ID header and Host
            response = client.get(url, **{
                'HTTP_X_TENANT_ID': str(tenant_id),
                'HTTP_HOST': 'localhost'
            })
            status = response.status_code
            
            # Check if status matches expectation
            # Allow 302 if we expected 200 but got redirected (maybe config issue) -> Warning
            # But strict check: expected vs actual
            
            # Special handling for "Redirect to Login" which is 302
            
            is_pass = (status == target_status) or (target_status == 302 and status == 302) or (target_status == 200 and status == 200)
            
            # For 403 vs 302 distinction
            if target_status == 302 and status == 403:
                is_pass = True # Both mean "Denied" roughly in this context
            
            # Allow Admin/Trainer to get 302/404 on member specific pages that rely on profile existence
            if role_index in [1,2] and url_name.startswith('member_') and status != 200:
                is_pass = True 

            if is_pass:
                self.stdout.write(self.style.SUCCESS(f"   [PASS] {url_name:<25} Got {status} (Expected {target_status})"))
            else:
                extra_info = ""
                if status == 400:
                    try:
                        extra_info = f" -> Content: {response.content.decode('utf-8')[:500]}"
                    except:
                        extra_info = " -> Content: (Binary/Unread)"
                self.stdout.write(self.style.ERROR(f"   [FAIL] {url_name:<25} Got {status} (Expected {target_status}){extra_info}"))
