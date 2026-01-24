from django.test import TestCase, Client
from django.urls import reverse
from core.models import CustomUser, MemberProfile, Tenant
from django.utils import timezone

class ComprehensiveNavigationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Test Gym", subdomain="testgym", contact_email="test@example.com")
        self.superuser = CustomUser.objects.create_superuser(username='admin', email='admin@test.com', password='password', role='admin', tenant=self.tenant)
        self.trainer = CustomUser.objects.create_user(username='trainer', email='trainer@test.com', password='password', role='trainer', tenant=self.tenant)
        self.member_user = CustomUser.objects.create_user(username='member', email='member@test.com', password='password', role='member', tenant=self.tenant)
        
        self.member_profile = MemberProfile.objects.create(
            user=self.member_user,
            tenant=self.tenant,
            membership_type='monthly',
            age=25,
            registration_amount=1000,
            monthly_amount=500,
            allotted_slot='Morning',
            registration_date=timezone.now().date(),
            next_payment_date=timezone.now().date() + timezone.timedelta(days=30)
        )

    def _test_navigation(self, user, url_name, expected_status=200, kwargs=None):
        self.client.force_login(user)
        url = reverse(url_name, kwargs=kwargs) if kwargs else reverse(url_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, expected_status, f"Failed for {url_name} as {user.role}. Got {response.status_code}")
        return response

    def test_admin_navigation(self):
        # Admin specific views
        self._test_navigation(self.superuser, 'member_list')
        self._test_navigation(self.superuser, 'add_member')
        self._test_navigation(self.superuser, 'trainer_list')
        self._test_navigation(self.superuser, 'add_trainer')
        self._test_navigation(self.superuser, 'finance')
        self._test_navigation(self.superuser, 'reports')
        self._test_navigation(self.superuser, 'notifications')
        self._test_navigation(self.superuser, 'branding_settings')
        self._test_navigation(self.superuser, 'staff_list')
        self._test_navigation(self.superuser, 'add_staff')
        self._test_navigation(self.superuser, 'add_payment')
        self._test_navigation(self.superuser, 'add_expense')
        self._test_navigation(self.superuser, 'bulk_import_members')
        self._test_navigation(self.superuser, 'download_member_import_sample')

    def test_trainer_navigation(self):
        # Trainer specific views
        self._test_navigation(self.trainer, 'trainer_attendance')
        self._test_navigation(self.trainer, 'upload_video')
        self._test_navigation(self.trainer, 'create_diet_plan')
        self._test_navigation(self.trainer, 'leave_request_list')

    def test_member_navigation(self):
        # Member specific views
        self._test_navigation(self.member_user, 'member_dashboard')
        self._test_navigation(self.member_user, 'member_attendance')
        self._test_navigation(self.member_user, 'member_payments')
        self._test_navigation(self.member_user, 'member_videos')
        self._test_navigation(self.member_user, 'member_diet')
        self._test_navigation(self.member_user, 'leave_request')

    def test_role_restricted_navigation(self):
        # Member trying to access admin pages (should redirect)
        self.client.force_login(self.member_user)
        response = self.client.get(reverse('trainer_list'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('dashboard')))

        # Trainer trying to access admin finance (should redirect)
        self.client.force_login(self.trainer)
        response = self.client.get(reverse('finance'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('dashboard')))
