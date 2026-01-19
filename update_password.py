import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_management.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

try:
    u = User.objects.get(username='admin')
    u.set_password('password')
    u.save()
    print('Password for user "admin" updated to "password".')
except User.DoesNotExist:
    print('User "admin" does not exist.')
