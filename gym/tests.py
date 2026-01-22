from django.test import TestCase, Client
from django.urls import reverse
from core.models import CustomUser, MemberProfile, Tenant
from django.utils import timezone

class ViewNavigationTests(TestCase):
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

    def test_admin_dashboard_access(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gym/admin_dashboard.html')

    def test_trainer_dashboard_access(self):
        self.client.force_login(self.trainer)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gym/trainer_dashboard.html')

    def test_member_dashboard_access(self):
        self.client.force_login(self.member_user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gym/member_dashboard.html')

    def test_member_list_access_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('member_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_member_list_access_denied_member(self):
        self.client.force_login(self.member_user)
        response = self.client.get(reverse('member_list'))
        # Should redirect to dashboard due to role_required decorator
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('dashboard')))

    def test_qr_code_generation(self):
        self.client.force_login(self.member_user)
        response = self.client.get(reverse('member_qr'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
