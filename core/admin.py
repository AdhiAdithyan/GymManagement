from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Tenant, BrandingConfig, CustomUser, MemberProfile, Attendance, Payment, 
    Expense, DietPlan, WorkoutVideo, ChatMessage, LeaveRequest, Subscription,
    TrainerSession, AuditLog
)

class MemberProfileInline(admin.StackedInline):
    model = MemberProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'tenant', 'is_staff')
    list_filter = ('role', 'tenant', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Tenant & Role', {'fields': ('tenant', 'role')}),
        ('Mobile', {'fields': ('device_id', 'push_token')}),
    )
    # inlines = [MemberProfileInline] # Optional: to show profile in user admin

# Register models
admin.site.register(Tenant)
admin.site.register(BrandingConfig)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MemberProfile)
admin.site.register(Attendance)
admin.site.register(Payment)
admin.site.register(Expense)
admin.site.register(DietPlan)
admin.site.register(WorkoutVideo)
admin.site.register(ChatMessage)
admin.site.register(LeaveRequest)
admin.site.register(Subscription)
admin.site.register(TrainerSession)
admin.site.register(AuditLog)

