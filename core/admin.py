from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Tenant, BrandingConfig, CustomUser, MemberProfile, Attendance, Payment, 
    Expense, DietPlan, WorkoutVideo, ChatMessage, LeaveRequest, Subscription,
    TrainerSession, AuditLog, WhatsAppMessage,
    # Payment Gateway Models
    PaymentGateway, SubscriptionPayment, PaymentMethod, PaymentWebhook,
    # Booking System Models
    ClassSchedule, ClassBooking, PersonalTrainingSession, BookingSettings,
    # Gamification Models
    Exercise, WorkoutLog, PersonalBest, Achievement, MemberEngagementScore,
    Leaderboard, Challenge, ChallengeParticipation
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

# Register existing models
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
admin.site.register(WhatsAppMessage)

# ============================================
# PHASE 1 MODERNIZATION - NEW MODELS
# ============================================

# Payment Gateway Models
@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'gateway_type', 'is_active', 'is_test_mode', 'created_at')
    list_filter = ('gateway_type', 'is_active', 'is_test_mode')
    search_fields = ('tenant__name',)

@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'status', 'payment_method', 'payment_date', 'transaction_id')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('member__user__username', 'transaction_id', 'invoice_number')
    readonly_fields = ('created_at', 'updated_at', 'gateway_response')

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('member', 'payment_type', 'card_last4', 'is_default', 'is_active')
    list_filter = ('payment_type', 'is_default', 'is_active')
    search_fields = ('member__user__username', 'card_last4')

@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = ('gateway', 'event_type', 'processed', 'received_at')
    list_filter = ('processed', 'gateway__gateway_type', 'received_at')
    search_fields = ('event_id', 'event_type')
    readonly_fields = ('payload', 'received_at')

# Booking System Models
@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'instructor', 'day_of_week', 'start_time', 'capacity', 'is_active')
    list_filter = ('day_of_week', 'class_type', 'is_active', 'tenant')
    search_fields = ('class_name', 'instructor__username')

@admin.register(ClassBooking)
class ClassBookingAdmin(admin.ModelAdmin):
    list_display = ('member', 'class_schedule', 'booking_date', 'status', 'booked_at')
    list_filter = ('status', 'booking_date', 'class_schedule__class_name')
    search_fields = ('member__user__username', 'class_schedule__class_name')
    readonly_fields = ('booked_at', 'cancelled_at', 'checked_in_at')

@admin.register(PersonalTrainingSession)
class PersonalTrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'member', 'session_date', 'start_time', 'status', 'rating')
    list_filter = ('status', 'session_type', 'session_date')
    search_fields = ('trainer__username', 'member__user__username')
    readonly_fields = ('booked_at', 'confirmed_at', 'completed_at')

@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'allow_member_booking', 'allow_waitlist', 'auto_confirm_bookings')
    list_filter = ('allow_member_booking', 'allow_waitlist')

# Gamification Models
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'measurement_type', 'difficulty_level', 'is_active')
    list_filter = ('category', 'measurement_type', 'difficulty_level', 'is_active')
    search_fields = ('name', 'description')

@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ('member', 'exercise', 'value', 'sets', 'reps', 'is_personal_best', 'logged_at')
    list_filter = ('is_personal_best', 'logged_at', 'exercise__category')
    search_fields = ('member__user__username', 'exercise__name')
    readonly_fields = ('logged_at',)

@admin.register(PersonalBest)
class PersonalBestAdmin(admin.ModelAdmin):
    list_display = ('member', 'exercise', 'best_value', 'achieved_date', 'times_improved')
    list_filter = ('achieved_date', 'exercise__category')
    search_fields = ('member__user__username', 'exercise__name')

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('member', 'title', 'achievement_type', 'points', 'earned_at')
    list_filter = ('achievement_type', 'earned_at')
    search_fields = ('member__user__username', 'title')

@admin.register(MemberEngagementScore)
class MemberEngagementScoreAdmin(admin.ModelAdmin):
    list_display = ('member', 'overall_score', 'churn_risk', 'last_visit_days_ago', 'calculated_at')
    list_filter = ('churn_risk', 'payment_status', 'calculated_at')
    search_fields = ('member__user__username',)
    readonly_fields = ('calculated_at',)

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('leaderboard_type', 'member', 'rank', 'score', 'period_start', 'period_end')
    list_filter = ('leaderboard_type', 'period_start')
    search_fields = ('member__user__username',)

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'challenge_type', 'start_date', 'end_date', 'status', 'reward_points')
    list_filter = ('status', 'challenge_type', 'start_date')
    search_fields = ('title', 'description')

@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    list_display = ('member', 'challenge', 'progress_percentage', 'is_completed', 'rank')
    list_filter = ('is_completed', 'challenge__status')
    search_fields = ('member__user__username', 'challenge__title')

