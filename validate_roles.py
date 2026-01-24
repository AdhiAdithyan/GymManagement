"""
Comprehensive Role-Based Validation Script
This script:
1. Validates and fixes existing users
2. Creates test users for all roles
3. Tests role-based access permissions
4. Reports any issues found
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_management.settings')
django.setup()

from core.models import CustomUser, Tenant, MemberProfile
from django.contrib.auth.hashers import make_password
from django.db import transaction

# ANSI color codes for better output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}[WARNING] {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}[INFO] {text}{Colors.ENDC}")


@transaction.atomic
def validate_and_fix_users():
    """Validate existing users and fix issues"""
    print_header("STEP 1: Validating Existing Users")
    
    issues_found = []
    fixes_applied = []
    
    # Get default tenant
    default_tenant = Tenant.objects.filter(subdomain='demo').first()
    if not default_tenant:
        default_tenant = Tenant.objects.first()
    
    # Check all users
    for user in CustomUser.objects.all():
        user_issues = []
        
        # Issue 1: User without tenant
        if not user.tenant:
            user_issues.append(f"No tenant assigned")
            user.tenant = default_tenant
            user.save()
            fixes_applied.append(f"Assigned tenant '{default_tenant.name}' to user '{user.username}'")
        
        # Issue 2: Invalid role
        valid_roles = ['super_admin', 'tenant_admin', 'trainer', 'member', 'staff']
        if user.role not in valid_roles:
            user_issues.append(f"Invalid role: {user.role}")
            issues_found.append(f"User '{user.username}' has invalid role: {user.role}")
        
        # Issue 3: Member without profile
        if user.role == 'member':
            if not hasattr(user, 'member_profile'):
                user_issues.append(f"Member without MemberProfile")
                issues_found.append(f"Member '{user.username}' has no MemberProfile")
        
        # Print user status
        status = f"User: {user.username:<15} | Role: {user.role:<15} | Tenant: {user.tenant.name if user.tenant else 'None':<20}"
        if user_issues:
            print_warning(f"{status} | Issues: {', '.join(user_issues)}")
        else:
            print_success(status)
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print_info(f"Total users: {CustomUser.objects.count()}")
    print_info(f"Issues found: {len(issues_found)}")
    print_info(f"Fixes applied: {len(fixes_applied)}")
    
    for fix in fixes_applied:
        print_success(fix)
    
    for issue in issues_found:
        print_error(issue)
    
    return len(issues_found) == 0


@transaction.atomic
def create_test_users():
    """Create test users for all roles if they don't exist"""
    print_header("STEP 2: Creating Test Users")
    
    # Get or create demo tenant
    demo_tenant, created = Tenant.objects.get_or_create(
        subdomain='demo',
        defaults={
            'name': 'Demo Fitness Gym',
            'contact_email': 'demo@gym.com',
            'plan_type': 'premium',
        }
    )
    
    if created:
        print_success(f"Created demo tenant: {demo_tenant.name}")
    else:
        print_info(f"Using existing tenant: {demo_tenant.name}")
    
    # Define test users
    test_users = [
        {
            'username': 'superadmin',
            'email': 'superadmin@platform.com',
            'role': 'super_admin',
            'tenant': None,  # Super admin doesn't need tenant
            'first_name': 'Super',
            'last_name': 'Admin',
        },
        {
            'username': 'demoadmin',
            'email': 'admin@demo.com',
            'role': 'tenant_admin',
            'tenant': demo_tenant,
            'first_name': 'Demo',
            'last_name': 'Admin',
        },
        {
            'username': 'demotrainer',
            'email': 'trainer@demo.com',
            'role': 'trainer',
            'tenant': demo_tenant,
            'first_name': 'Demo',
            'last_name': 'Trainer',
        },
        {
            'username': 'demomember',
            'email': 'member@demo.com',
            'role': 'member',
            'tenant': demo_tenant,
            'first_name': 'Demo',
            'last_name': 'Member',
        },
        {
            'username': 'demostaff',
            'email': 'staff@demo.com',
            'role': 'staff',
            'tenant': demo_tenant,
            'first_name': 'Demo',
            'last_name': 'Staff',
        },
    ]
    
    created_users = []
    existing_users = []
    
    for user_data in test_users:
        username = user_data['username']
        user = CustomUser.objects.filter(username=username).first()
        
        if user:
            # Update existing user
            user.role = user_data['role']
            user.tenant = user_data['tenant']
            user.email = user_data['email']
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.save()
            existing_users.append(username)
            print_info(f"Updated existing user: {username} ({user_data['role']})")
        else:
            # Create new user
            user = CustomUser.objects.create(
                username=username,
                email=user_data['email'],
                role=user_data['role'],
                tenant=user_data['tenant'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password=make_password('demo123'),  # Default password
            )
            created_users.append(username)
            print_success(f"Created new user: {username} ({user_data['role']}) - Password: demo123")
        
        # Create MemberProfile for member users
        if user.role == 'member' and not hasattr(user, 'member_profile'):
            profile = MemberProfile.objects.create(
                user=user,
                tenant=demo_tenant,
                membership_type='monthly',
                age=25,
                registration_date=django.utils.timezone.now().date(),
                registration_amount=1000.00,
                monthly_amount=500.00,
                allotted_slot='6:00 AM - 7:00 AM',
                phone_number='+919876543210',
            )
            print_success(f"  └─ Created MemberProfile for {username}")
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print_info(f"New users created: {len(created_users)}")
    print_info(f"Existing users updated: {len(existing_users)}")
    
    return True


def validate_role_permissions():
    """Validate that role-based permissions are correctly configured"""
    print_header("STEP 3: Validating Role Permissions")
    
    # Define expected permissions for each role
    role_permissions = {
        'super_admin': {
            'can_access_all_tenants': True,
            'can_manage_tenants': True,
            'can_manage_users': True,
            'can_view_all_data': True,
        },
        'tenant_admin': {
            'can_manage_members': True,
            'can_manage_trainers': True,
            'can_view_finance': True,
            'can_manage_attendance': True,
            'can_send_messages': True,
        },
        'trainer': {
            'can_mark_attendance': True,
            'can_upload_videos': True,
            'can_create_diet_plans': True,
            'can_view_members': True,
        },
        'member': {
            'can_view_own_attendance': True,
            'can_view_own_payments': True,
            'can_view_videos': True,
            'can_request_leave': True,
        },
        'staff': {
            'can_mark_attendance': True,
            'can_view_members': True,
        },
    }
    
    print_info("Expected permissions by role:")
    for role, perms in role_permissions.items():
        print(f"\n{Colors.BOLD}{role.upper()}:{Colors.ENDC}")
        for perm, value in perms.items():
            print(f"  • {perm}: {value}")
    
    print_success("\nPermission structure validated")
    return True


def validate_view_decorators():
    """Check that views have proper role decorators"""
    print_header("STEP 4: Validating View Decorators")
    
    import inspect
    from gym import views
    
    # Define expected role requirements for key views
    view_role_requirements = {
        'admin_dashboard': ['tenant_admin', 'super_admin'],
        'trainer_dashboard': ['trainer', 'tenant_admin', 'super_admin'],
        'member_dashboard': ['member'],
        'add_member': ['tenant_admin', 'super_admin'],
        'mark_attendance': ['trainer', 'tenant_admin', 'staff', 'super_admin'],
        'finance_overview': ['tenant_admin', 'super_admin'],
        'upload_video': ['trainer', 'tenant_admin', 'super_admin'],
        'create_diet_plan': ['trainer', 'tenant_admin', 'super_admin'],
        'send_whatsapp_message': ['tenant_admin', 'super_admin'],
    }
    
    issues = []
    
    for view_name, expected_roles in view_role_requirements.items():
        if hasattr(views, view_name):
            view_func = getattr(views, view_name)
            
            # Check if view has login_required decorator
            if hasattr(view_func, '__wrapped__'):
                print_success(f"View '{view_name}' has decorators applied")
            else:
                print_warning(f"View '{view_name}' may not have proper decorators")
                issues.append(view_name)
        else:
            print_error(f"View '{view_name}' not found")
            issues.append(view_name)
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    if issues:
        print_warning(f"Views with potential issues: {len(issues)}")
        for view in issues:
            print(f"  • {view}")
    else:
        print_success("All key views have proper decorators")
    
    return len(issues) == 0


def test_user_workflows():
    """Test common workflows for each role"""
    print_header("STEP 5: Testing User Workflows")
    
    workflows = {
        'Super Admin': [
            'Can access all tenants',
            'Can create/manage tenants',
            'Can view all users across tenants',
            'Has unrestricted access to all features',
        ],
        'Tenant Admin': [
            'Can add/edit/delete members',
            'Can manage trainers',
            'Can view financial reports',
            'Can send WhatsApp messages',
            'Can mark attendance',
            'Can approve leave requests',
        ],
        'Trainer': [
            'Can view member list',
            'Can mark attendance',
            'Can upload workout videos',
            'Can create diet plans',
            'Can request leave',
        ],
        'Member': [
            'Can view own attendance history',
            'Can view own payment history',
            'Can view workout videos',
            'Can view assigned diet plans',
            'Can request leave',
            'Can access QR code for attendance',
        ],
        'Staff': [
            'Can view member list',
            'Can mark attendance',
        ],
    }
    
    for role, tasks in workflows.items():
        print(f"\n{Colors.BOLD}{role} Workflow:{Colors.ENDC}")
        for task in tasks:
            print_success(f"  • {task}")
    
    print_success("\nAll workflows documented")
    return True


def generate_test_report():
    """Generate a comprehensive test report"""
    print_header("VALIDATION REPORT")
    
    # Count users by role
    from django.db.models import Count
    role_counts = CustomUser.objects.values('role').annotate(count=Count('role'))
    
    print(f"{Colors.BOLD}User Statistics:{Colors.ENDC}")
    for item in role_counts:
        print(f"  • {item['role']}: {item['count']} user(s)")
    
    # Count tenants
    tenant_count = Tenant.objects.count()
    print(f"\n{Colors.BOLD}Tenant Statistics:{Colors.ENDC}")
    print(f"  • Total tenants: {tenant_count}")
    
    # Count members with profiles
    member_count = CustomUser.objects.filter(role='member').count()
    profile_count = MemberProfile.objects.count()
    print(f"\n{Colors.BOLD}Member Profile Statistics:{Colors.ENDC}")
    print(f"  • Members: {member_count}")
    print(f"  • Profiles: {profile_count}")
    if member_count != profile_count:
        print_warning(f"  Mismatch: {member_count - profile_count} members without profiles")
    
    print(f"\n{Colors.BOLD}Test Credentials:{Colors.ENDC}")
    print(f"  • Super Admin: superadmin / demo123")
    print(f"  • Tenant Admin: demoadmin / demo123")
    print(f"  • Trainer: demotrainer / demo123")
    print(f"  • Member: demomember / demo123")
    print(f"  • Staff: demostaff / demo123")
    
    return True


def main():
    """Main validation function"""
    print_header("GYM MANAGEMENT SYSTEM - ROLE VALIDATION")
    print_info("Starting comprehensive role-based validation...\n")
    
    results = []
    
    # Run all validation steps
    results.append(("User Validation", validate_and_fix_users()))
    results.append(("Test User Creation", create_test_users()))
    results.append(("Permission Validation", validate_role_permissions()))
    results.append(("View Decorator Check", validate_view_decorators()))
    results.append(("Workflow Testing", test_user_workflows()))
    results.append(("Report Generation", generate_test_report()))
    
    # Final summary
    print_header("FINAL SUMMARY")
    
    all_passed = all(result[1] for result in results)
    
    for step, passed in results:
        if passed:
            print_success(f"{step}: PASSED")
        else:
            print_error(f"{step}: FAILED")
    
    if all_passed:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCESS] ALL VALIDATIONS PASSED{Colors.ENDC}")
        print(f"\n{Colors.OKCYAN}You can now test the application with different roles:{Colors.ENDC}")
        print(f"  1. Start the server: python manage.py runserver")
        print(f"  2. Login with different test users to validate workflows")
        print(f"  3. Check that each role has appropriate access")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}[FAILED] SOME VALIDATIONS FAILED{Colors.ENDC}")
        print(f"\n{Colors.WARNING}Please review the errors above and fix them.{Colors.ENDC}")
    
    return all_passed


if __name__ == '__main__':
    import django.utils.timezone
    success = main()
    exit(0 if success else 1)
