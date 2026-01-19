from django.core.management.base import BaseCommand
from core.models import Tenant, BrandingConfig, CustomUser, MemberProfile
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Create demo tenant for testing the SaaS platform'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creating demo tenant...'))
        
        # Create tenant
        tenant, created = Tenant.objects.get_or_create(
            subdomain='demo',
            defaults={
                'name': 'Demo Fitness Gym',
                'contact_email': 'admin@demogym.com',
                'contact_phone': '+1234567890',
                'plan_type': 'premium',
                'trial_ends_at': timezone.now().date() + timedelta(days=30),
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'[+] Created tenant: {tenant.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'[!] Tenant already exists: {tenant.name}'))
        
        # Create branding
        branding, created = BrandingConfig.objects.get_or_create(
            tenant=tenant,
            defaults={
                'app_name': 'Demo Gym App',
                'primary_color': '#FF5722',
                'secondary_color': '#03DAC6',
                'accent_color': '#FFC107',
                'features': {
                    'attendance': True,
                    'payments': True,
                    'workout_videos': True,
                    'diet_plans': True,
                    'leave_requests': True,
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'[+] Created branding config'))
        else:
            self.stdout.write(self.style.WARNING(f'[!] Branding already exists'))
        
        # Create tenant admin user
        admin_user, created = CustomUser.objects.get_or_create(
            username='demoadmin',
            defaults={
                'tenant': tenant,
                'email': 'admin@demogym.com',
                'role': 'tenant_admin',
                'first_name': 'Admin',
                'last_name': 'User',
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.tenant = tenant
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'[+] Created admin user: demoadmin / admin123'))
        else:
            self.stdout.write(self.style.WARNING(f'[!] Admin user already exists'))
        
        # Create a trainer user
        trainer_user, created = CustomUser.objects.get_or_create(
            username='demotrainer',
            defaults={
                'tenant': tenant,
                'email': 'trainer@demogym.com',
                'role': 'trainer',
                'first_name': 'John',
                'last_name': 'Trainer',
            }
        )
        
        if created:
            trainer_user.set_password('trainer123')
            trainer_user.tenant = tenant
            trainer_user.save()
            self.stdout.write(self.style.SUCCESS(f'[+] Created trainer user: demotrainer / trainer123'))
        else:
            self.stdout.write(self.style.WARNING(f'[!] Trainer user already exists'))
        
        # Create a member user
        member_user, created = CustomUser.objects.get_or_create(
            username='demomember',
            defaults={
                'tenant': tenant,
                'email': 'member@demogym.com',
                'role': 'member',
                'first_name': 'Jane',
                'last_name': 'Member',
            }
        )
        
        if created:
            member_user.set_password('member123')
            member_user.tenant = tenant
            member_user.save()
            self.stdout.write(self.style.SUCCESS(f'[+] Created member user: demomember / member123'))
            
            # Create member profile
            profile = MemberProfile.objects.create(
                tenant=tenant,
                user=member_user,
                age=25,
                membership_type='monthly',
                occupation='Software Engineer',
                registration_date=timezone.now().date(),
                next_payment_date=timezone.now().date() + timedelta(days=30),
                registration_amount=500.00,
                monthly_amount=100.00,
                allotted_slot='6:00 AM - 7:00 AM'
            )
            self.stdout.write(self.style.SUCCESS(f'[+] Created member profile'))
        else:
            self.stdout.write(self.style.WARNING(f'[!] Member user already exists'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Demo Tenant Created ==='))
        self.stdout.write(f'Tenant ID: {tenant.id}')
        self.stdout.write(f'Subdomain: {tenant.subdomain}')
        self.stdout.write(f'')
        self.stdout.write('Test Users:')
        self.stdout.write(f'  Admin:   demoadmin / admin123')
        self.stdout.write(f'  Trainer: demotrainer / trainer123')
        self.stdout.write(f'  Member:  demomember / member123')
        self.stdout.write('')
        self.stdout.write('API Usage:')
        self.stdout.write(f'  Add header: X-Tenant-ID: {tenant.id}')
        self.stdout.write(f'  Or use subdomain: demo.yourdomain.com')
