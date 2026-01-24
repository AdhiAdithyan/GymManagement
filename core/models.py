from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Tenant(models.Model):
    """Multi-tenant support - each gym is a tenant"""
    name = models.CharField(max_length=200)
    subdomain = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Contact info
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Subscription info
    plan_type = models.CharField(
        max_length=20,
        choices=[('trial', 'Trial'), ('basic', 'Basic'), ('premium', 'Premium'), ('enterprise', 'Enterprise')],
        default='trial'
    )
    trial_ends_at = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenants'
        indexes = [models.Index(fields=['subdomain'])]
    
    def __str__(self):
        return self.name

class BrandingConfig(models.Model):
    """White-labeling configuration per tenant"""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='branding')
    
    # App branding
    app_name = models.CharField(max_length=100, default='Gym App')
    logo = models.ImageField(upload_to='branding/logos/', null=True, blank=True)
    app_icon = models.ImageField(upload_to='branding/icons/', null=True, blank=True)
    
    # Color scheme (hex codes)
    primary_color = models.CharField(max_length=7, default='#6200EA')
    secondary_color = models.CharField(max_length=7, default='#03DAC6')
    accent_color = models.CharField(max_length=7, default='#FF5722')
    
    # Feature toggles
    features = models.JSONField(default=dict, help_text="Feature flags as JSON")
    
    class Meta:
        db_table = 'branding_configs'
    
    def __str__(self):
        return f"{self.tenant.name} Branding"

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),  # Platform owner
        ('tenant_admin', 'Tenant Admin'),  # Gym owner
        ('trainer', 'Trainer'),
        ('member', 'Member'),
        ('staff', 'Staff'),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Mobile app support
    device_id = models.CharField(max_length=255, blank=True, help_text="Mobile device identifier")
    push_token = models.CharField(max_length=255, blank=True, help_text="Push notification token")
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['tenant', 'role']),
            models.Index(fields=['email', 'tenant']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class MemberProfile(models.Model):
    MEMBERSHIP_TYPES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='members', null=True, blank=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='member_profile')
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_TYPES)
    age = models.PositiveIntegerField()
    occupation = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='members/', blank=True, null=True)
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Phone number in international format (e.g., +1234567890)"
    )
    registration_date = models.DateField(default=timezone.now)
    next_payment_date = models.DateField(blank=True, null=True) # Allow blank for initial calculation
    registration_amount = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    allotted_slot = models.CharField(max_length=50, help_text="e.g. 6:00 AM - 7:00 AM")
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"
    
    @staticmethod
    def validate_phone(phone_number):
        """
        Validates and cleans a phone number. 
        Returns the cleaned number if valid, raises ValidationError if not.
        """
        from django.core.exceptions import ValidationError
        import re
        
        if not phone_number:
            return None
            
        # Remove spaces and dashes for validation
        phone = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Check if it starts with + and has 10-15 digits
        if not re.match(r'^\+\d{10,15}$', phone):
            raise ValidationError('Phone number must be in international format (e.g., +1234567890)')
            
        return phone

    def clean(self):
        """Validate phone number format"""
        from django.core.exceptions import ValidationError
        
        if self.phone_number:
            try:
                self.phone_number = MemberProfile.validate_phone(self.phone_number)
            except ValidationError as e:
                raise ValidationError({'phone_number': e.message})

class Attendance(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    check_in_time = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='Present')

class Payment(models.Model):
    PAYMENT_TYPES = (
        ('registration', 'Registration Fee'),
        ('monthly', 'Monthly Fee'),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    remarks = models.TextField(blank=True)

class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('maintenance', 'Maintenance'),
        ('salary', 'Salary'),
        ('electricity', 'Electricity'),
        ('other', 'Other'),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField()

class DietPlan(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='diet_plans', null=True, blank=True)
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='assigned_diets')

class WorkoutVideo(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=100)
    video_file = models.FileField(upload_to='videos/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    target_audience = models.CharField(max_length=50, choices=[('all', 'All'), ('beginner', 'Beginner'), ('advanced', 'Advanced')], default='all')

class ChatMessage(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    room_name = models.CharField(max_length=50, blank=True, null=True, help_text="For group chats")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.user.username} - {self.status}"

class Subscription(models.Model):
    """Replace direct membership_type with subscription model"""
    PLAN_CHOICES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
    )
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    )
    
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    auto_renewal = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.member.user.username} - {self.plan} ({self.status})"

class TrainerSession(models.Model):
    """Trainer session scheduling"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    trainer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='sessions')
    
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    session_type = models.CharField(max_length=50, choices=[
        ('personal', 'Personal Training'),
        ('group', 'Group Class'),
        ('assessment', 'Assessment'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='scheduled')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'trainer_sessions'
        ordering = ['-session_date', '-start_time']
    
    def __str__(self):
        return f"{self.trainer.username} -> {self.member.user.username} on {self.session_date}"

class AuditLog(models.Model):
    """Security audit logging"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.IntegerField(null=True, blank=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"

class WhatsAppMessage(models.Model):
    """Log of WhatsApp messages sent to members"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    sent_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='sent_whatsapp_messages')
    recipients = models.JSONField(default=list, help_text="List of member IDs who received the message")
    time_slot = models.CharField(max_length=50, blank=True, help_text="Target time slot, or 'all' for all members")
    message_content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    recipient_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'whatsapp_messages'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"WhatsApp to {self.time_slot} by {self.sent_by} at {self.sent_at}"


# Import new model modules for Phase 1 Modernization
# These models are defined in separate files for better organization

# Payment Gateway Models
from .payment_models import (
    PaymentGateway,
    SubscriptionPayment,
    PaymentMethod,
    PaymentWebhook
)

# Booking System Models
from .booking_models import (
    ClassSchedule,
    ClassBooking,
    PersonalTrainingSession,
    BookingSettings
)

# Gamification Models
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
