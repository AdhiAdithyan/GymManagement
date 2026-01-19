from rest_framework import serializers
from core.models import (
    CustomUser, MemberProfile, Attendance, Payment, 
    DietPlan, WorkoutVideo, LeaveRequest, Subscription,
    TrainerSession, BrandingConfig, Tenant
)


class BrandingSerializer(serializers.ModelSerializer):
    """Tenant branding configuration"""
    
    class Meta:
        model = BrandingConfig
        fields = ['app_name', 'logo', 'app_icon', 'primary_color', 
                  'secondary_color', 'accent_color', 'features']


class UserSerializer(serializers.ModelSerializer):
    """Basic user information"""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'role']


class MemberProfileSerializer(serializers.ModelSerializer):
    """Member profile with user details"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberProfile
        fields = ['id', 'username', 'email', 'full_name', 'age', 'occupation', 'image',
                  'membership_type',  'allotted_slot', 'registration_date', 'next_payment_date']
        read_only_fields = ['id', 'registration_date']
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class MemberDashboardSerializer(serializers.Serializer):
    """Member mobile dashboard data"""
    profile = MemberProfileSerializer()
    total_attendance = serializers.IntegerField()
    payment_due_days = serializers.IntegerField(allow_null=True)
    active_subscription = serializers.DictField(allow_null=True)
    recent_payments = serializers.ListField()


class AttendanceSerializer(serializers.ModelSerializer):
    """Attendance record"""
    member_name = serializers.CharField(source='member.user.username', read_only=True)
    member_id = serializers.IntegerField(source='member.id', read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'member', 'member_id', 'member_name', 'date', 'check_in_time', 'status']
        read_only_fields = ['id', 'date', 'check_in_time']


class PaymentSerializer(serializers.ModelSerializer):
    """Payment record"""
    member_name = serializers.CharField(source='member.user.username', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'member_name', 'amount', 'date', 'payment_type', 'remarks']
        read_only_fields = ['id', 'date']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Subscription information"""
    member_name = serializers.CharField(source='member.user.username', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = ['id', 'member_name', 'plan', 'status', 'start_date', 'end_date', 
                  'amount', 'auto_renewal', 'days_remaining', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_days_remaining(self, obj):
        from django.utils import timezone
        if obj.end_date:
            delta = obj.end_date - timezone.now().date()
            return delta.days if delta.days >= 0 else 0
        return None


class DietPlanSerializer(serializers.ModelSerializer):
    """Diet plan details"""
    assigned_by_name = serializers.CharField(source='assigned_by.username', read_only=True)
    member_name = serializers.CharField(source='member.user.username', read_only=True)
    
    class Meta:
        model = DietPlan
        fields = ['id', 'member_name', 'title', 'content', 'created_at', 'assigned_by_name']
        read_only_fields = ['id', 'created_at', 'assigned_by_name']


class WorkoutVideoSerializer(serializers.ModelSerializer):
    """Workout video details"""
    video_url = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkoutVideo
        fields = ['id', 'title', 'video_file', 'video_url', 'description', 
                  'uploaded_at', 'target_audience']
        read_only_fields = ['id', 'uploaded_at']
    
    def get_video_url(self, obj):
        if obj.video_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video_file.url)
        return None


class TrainerSessionSerializer(serializers.ModelSerializer):
    """Trainer session details"""
    trainer_name = serializers.CharField(source='trainer.username', read_only=True)
    member_name = serializers.CharField(source='member.user.username', read_only=True)
    
    class Meta:
        model = TrainerSession
        fields = ['id', 'trainer_name', 'member', 'member_name', 'session_date',
                  'start_time', 'end_time', 'session_type', 'status', 'notes']
        read_only_fields = ['id', 'trainer_name']


class LeaveRequestSerializer(serializers.ModelSerializer):
    """Leave request details"""
    member_name = serializers.CharField(source='member.user.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = LeaveRequest
        fields = ['id', 'member_name', 'start_date', 'end_date', 
                  'reason', 'status', 'approved_by_name', 'created_at']
        read_only_fields = ['id', 'created_at', 'status', 'approved_by_name']


class TrainerDashboardSerializer(serializers.Serializer):
    """Trainer dashboard statistics"""
    total_members = serializers.IntegerField()
    today_sessions = TrainerSessionSerializer(many=True)
    pending_sessions = serializers.IntegerField()
