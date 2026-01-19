"""
Quick script to update existing admin user to tenant_admin role
Run this once: python update_admin_roles.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_management.settings')
django.setup()

from core.models import CustomUser, Tenant

# Get or create a default tenant for existing users
tenant, created = Tenant.objects.get_or_create(
    subdomain='main',
    defaults={
        'name': 'Main Gym',
        'contact_email': 'admin@maingym.com',
        'plan_type': 'enterprise',
    }
)

if created:
    print(f"Created default tenant: {tenant.name}")
else:
    print(f"Using existing tenant: {tenant.name}")

# Update all users with 'admin' role to 'tenant_admin'
admin_users = CustomUser.objects.filter(role='admin')
count = admin_users.count()

for user in admin_users:
    user.role = 'tenant_admin'
    if not user.tenant:
        user.tenant = tenant
    user.save()
    print(f"Updated user: {user.username} -> tenant_admin")

# Update superusers
superusers = CustomUser.objects.filter(is_superuser=True, tenant=None)
for user in superusers:
    user.tenant = tenant
    if user.role == 'admin':
        user.role = 'tenant_admin'
    user.save()
    print(f"Updated superuser: {user.username}")

# Update users without tenant
users_without_tenant = CustomUser.objects.filter(tenant=None)
for user in users_without_tenant:
    user.tenant = tenant
    user.save()
    print(f"Assigned tenant to: {user.username}")

print(f"\nTotal users updated: {count}")
print(f"Tenant ID: {tenant.id}")
print("\nYou can now log in with your existing credentials!")
