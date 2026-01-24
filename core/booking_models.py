"""
Booking System Models for Class Scheduling and Member Bookings
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Tenant, CustomUser, MemberProfile


class ClassSchedule(models.Model):
    """Recurring class schedule template"""
    DAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    CLASS_TYPE_CHOICES = (
        ('yoga', 'Yoga'),
        ('zumba', 'Zumba'),
        ('crossfit', 'CrossFit'),
        ('spinning', 'Spinning'),
        ('pilates', 'Pilates'),
        ('hiit', 'HIIT'),
        ('strength', 'Strength Training'),
        ('cardio', 'Cardio'),
        ('martial_arts', 'Martial Arts'),
        ('other', 'Other'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='class_schedules')
    
    class_name = models.CharField(max_length=100)
    class_type = models.CharField(max_length=50, choices=CLASS_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    instructor = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='teaching_classes',
        limit_choices_to={'role__in': ['trainer', 'tenant_admin']}
    )
    
    # Recurring schedule
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Capacity management
    capacity = models.IntegerField(default=20, help_text="Maximum number of participants")
    waitlist_capacity = models.IntegerField(default=5, help_text="Maximum waitlist size")
    
    # Booking rules
    booking_opens_days_before = models.IntegerField(default=7, help_text="Days before class when booking opens")
    booking_closes_hours_before = models.IntegerField(default=2, help_text="Hours before class when booking closes")
    cancellation_allowed_hours_before = models.IntegerField(default=4, help_text="Hours before class when cancellation is allowed")
    
    # Status
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(default=timezone.now)
    effective_until = models.DateField(null=True, blank=True)
    
    # Metadata
    color_code = models.CharField(max_length=7, default='#6200EA', help_text="Hex color for calendar display")
    image = models.ImageField(upload_to='classes/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'class_schedules'
        ordering = ['day_of_week', 'start_time']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['day_of_week', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.class_name} - {self.get_day_of_week_display()} {self.start_time}"
    
    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")


class ClassBooking(models.Model):
    """Individual class bookings by members"""
    STATUS_CHOICES = (
        ('confirmed', 'Confirmed'),
        ('waitlist', 'Waitlist'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
    )
    
    class_schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE, related_name='bookings')
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='class_bookings')
    
    booking_date = models.DateField(help_text="Specific date of the class")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    
    # Booking metadata
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Attendance tracking
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    # Waitlist management
    waitlist_position = models.IntegerField(null=True, blank=True)
    promoted_from_waitlist_at = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'class_bookings'
        ordering = ['-booking_date', 'waitlist_position']
        unique_together = ['class_schedule', 'member', 'booking_date']
        indexes = [
            models.Index(fields=['member', 'status']),
            models.Index(fields=['booking_date', 'status']),
            models.Index(fields=['class_schedule', 'booking_date']),
        ]
    
    def __str__(self):
        return f"{self.member.user.username} - {self.class_schedule.class_name} on {self.booking_date}"
    
    def can_cancel(self):
        """Check if booking can be cancelled based on cancellation policy"""
        if self.status in ['cancelled', 'attended', 'no_show']:
            return False
        
        from datetime import datetime, timedelta
        class_datetime = datetime.combine(
            self.booking_date,
            self.class_schedule.start_time
        )
        cancellation_deadline = class_datetime - timedelta(
            hours=self.class_schedule.cancellation_allowed_hours_before
        )
        
        return timezone.now() < cancellation_deadline
    
    def cancel(self, reason=''):
        """Cancel the booking and promote waitlist if applicable"""
        if not self.can_cancel():
            raise ValidationError("Cancellation deadline has passed")
        
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()
        
        # Promote from waitlist
        if self.status == 'confirmed':
            self._promote_from_waitlist()
    
    def _promote_from_waitlist(self):
        """Promote next person from waitlist"""
        next_waitlist = ClassBooking.objects.filter(
            class_schedule=self.class_schedule,
            booking_date=self.booking_date,
            status='waitlist'
        ).order_by('waitlist_position').first()
        
        if next_waitlist:
            next_waitlist.status = 'confirmed'
            next_waitlist.promoted_from_waitlist_at = timezone.now()
            next_waitlist.waitlist_position = None
            next_waitlist.save()
            
            # TODO: Send notification to promoted member


class PersonalTrainingSession(models.Model):
    """One-on-one personal training sessions (enhanced from TrainerSession)"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='pt_sessions')
    trainer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='pt_sessions',
        limit_choices_to={'role__in': ['trainer', 'tenant_admin']}
    )
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='pt_sessions')
    
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    session_type = models.CharField(max_length=50, choices=[
        ('assessment', 'Initial Assessment'),
        ('strength', 'Strength Training'),
        ('cardio', 'Cardio Training'),
        ('flexibility', 'Flexibility & Mobility'),
        ('nutrition', 'Nutrition Consultation'),
        ('general', 'General Training'),
    ], default='general')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Session details
    goals = models.TextField(blank=True, help_text="Session goals")
    notes = models.TextField(blank=True, help_text="Trainer notes")
    member_feedback = models.TextField(blank=True, help_text="Member feedback after session")
    rating = models.IntegerField(null=True, blank=True, help_text="Member rating 1-5")
    
    # Booking management
    booked_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Reminders
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'personal_training_sessions'
        ordering = ['-session_date', '-start_time']
        indexes = [
            models.Index(fields=['trainer', 'session_date']),
            models.Index(fields=['member', 'session_date']),
            models.Index(fields=['session_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.trainer.username} -> {self.member.user.username} on {self.session_date}"
    
    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")


class BookingSettings(models.Model):
    """Tenant-specific booking configuration"""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='booking_settings')
    
    # Class booking settings
    allow_member_booking = models.BooleanField(default=True)
    allow_waitlist = models.BooleanField(default=True)
    auto_confirm_bookings = models.BooleanField(default=True)
    
    # Cancellation policy
    allow_cancellation = models.BooleanField(default=True)
    cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Limits
    max_bookings_per_member_per_day = models.IntegerField(default=3)
    max_bookings_per_member_per_week = models.IntegerField(default=10)
    
    # Notifications
    send_booking_confirmation = models.BooleanField(default=True)
    send_reminder_24h_before = models.BooleanField(default=True)
    send_reminder_2h_before = models.BooleanField(default=False)
    send_waitlist_promotion_notification = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_settings'
    
    def __str__(self):
        return f"Booking Settings - {self.tenant.name}"
