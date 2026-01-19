from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from django.db.models import Count, Q
from core.models import *
from .serializers import *
from .permissions import IsTenantUser, IsMember, IsTrainer, IsTenantAdmin


# ==================== Authentication ====================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer to include user info"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'tenant_id': self.user.tenant_id if self.user.tenant else None,
        }
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login endpoint with tenant validation"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
@permission_classes([AllowAny])
def get_branding(request):
    """Get tenant branding configuration"""
    tenant = request.tenant
    if not tenant:
        return Response({'error': 'Tenant not found'}, status=404)
    
    branding = BrandingConfig.objects.filter(tenant=tenant).first()
    if branding:
        serializer = BrandingSerializer(branding, context={'request': request})
        return Response(serializer.data)
    
    # Return default branding
    return Response({
        'app_name': tenant.name,
        'primary_color': '#6200EA',
        'secondary_color': '#03DAC6',
        'accent_color': '#FF5722',
        'features': {}
    })


# ==================== Member APIs ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsMember])
def member_dashboard(request):
    """Get member dashboard data"""
    try:
        member = request.user.member_profile
    except MemberProfile.DoesNotExist:
        return Response({'error': 'Member profile not found'}, status=404)
    
    today = timezone.now().date()
    
    # Calculate stats
    total_attendance = Attendance.objects.filter(
        member=member, 
        status='Present'
    ).count()
    
    payment_due_days = None
    if member.next_payment_date:
        payment_due_days = (member.next_payment_date - today).days
    
    # Active subscription
    active_sub = Subscription.objects.filter(
        member=member, 
        status='active'
    ).first()
    
    # Recent payments
    recent_payments = Payment.objects.filter(member=member).order_by('-date')[:5]
    
    data = {
        'profile': MemberProfileSerializer(member, context={'request': request}).data,
        'total_attendance': total_attendance,
        'payment_due_days': payment_due_days,
        'active_subscription': SubscriptionSerializer(active_sub, context={'request': request}).data if active_sub else None,
        'recent_payments': PaymentSerializer(recent_payments, many=True, context={'request': request}).data,
    }
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsMember])
def member_check_in(request):
    """Member self check-in"""
    try:
        member = request.user.member_profile
    except MemberProfile.DoesNotExist:
        return Response({'error': 'Member profile not found'}, status=404)
    
    today = timezone.now().date()
    
    # Check if already checked in today
    exists = Attendance.objects.filter(
        member=member, 
        date=today
    ).exists()
    
    if exists:
        return Response(
            {'detail': 'Already checked in today'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    attendance = Attendance.objects.create(
        tenant=request.tenant,
        member=member,
        date=today,
        status='Present'
    )
    
    return Response(
        AttendanceSerializer(attendance, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


class MemberAttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """Member attendance history"""
    permission_classes = [IsAuthenticated, IsMember]
    serializer_class = AttendanceSerializer
    
    def get_queryset(self):
        return Attendance.objects.filter(
            member=self.request.user.member_profile
        ).order_by('-date')


class MemberPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Member payment history"""
    permission_classes = [IsAuthenticated, IsMember]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        return Payment.objects.filter(
            member=self.request.user.member_profile
        ).order_by('-date')


class MemberDietPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """Member diet plans"""
    permission_classes = [IsAuthenticated, IsMember]
    serializer_class = DietPlanSerializer
    
    def get_queryset(self):
        return DietPlan.objects.filter(
            member=self.request.user.member_profile
        ).order_by('-created_at')


class MemberWorkoutVideoViewSet(viewsets.ReadOnlyModelViewSet):
    """Member workout videos"""
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutVideoSerializer
    
    def get_queryset(self):
        queryset = WorkoutVideo.objects.all().order_by('-uploaded_at')
        if self.request.tenant:
            queryset = queryset.filter(tenant=self.request.tenant)
        return queryset


class MemberLeaveRequestViewSet(viewsets.ModelViewSet):
    """Member leave requests"""
    permission_classes = [IsAuthenticated, IsMember]
    serializer_class = LeaveRequestSerializer
    
    def get_queryset(self):
        return LeaveRequest.objects.filter(
            member=self.request.user.member_profile
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant,
            member=self.request.user.member_profile
        )


# ==================== Trainer APIs ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTrainer])
def trainer_dashboard(request):
    """Get trainer dashboard data"""
    tenant = request.tenant
    today = timezone.now().date()
    
    total_members = MemberProfile.objects.filter(tenant=tenant).count() if tenant else 0
    
    today_sessions = TrainerSession.objects.filter(
        trainer=request.user,
        session_date=today
    )
    
    pending_sessions = TrainerSession.objects.filter(
        trainer=request.user,
        status='scheduled',
        session_date__gte=today
    ).count()
    
    data = {
        'total_members': total_members,
        'today_sessions': TrainerSessionSerializer(today_sessions, many=True, context={'request': request}).data,
        'pending_sessions': pending_sessions,
    }
    
    return Response(data)


class TrainerMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """Trainer view of members"""
    permission_classes = [IsAuthenticated, IsTrainer]
    serializer_class = MemberProfileSerializer
    
    def get_queryset(self):
        queryset = MemberProfile.objects.all().select_related('user')
        if self.request.tenant:
            queryset = queryset.filter(tenant=self.request.tenant)
        return queryset


class TrainerAttendanceViewSet(viewsets.ModelViewSet):
    """Trainer attendance management"""
    permission_classes = [IsAuthenticated, IsTrainer]
    serializer_class = AttendanceSerializer
    
    def get_queryset(self):
        queryset = Attendance.objects.all().select_related('member__user').order_by('-date', '-check_in_time')
        if self.request.tenant:
            queryset = queryset.filter(tenant=self.request.tenant)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


class TrainerSessionViewSet(viewsets.ModelViewSet):
    """Trainer session management"""
    permission_classes = [IsAuthenticated, IsTrainer]
    serializer_class = TrainerSessionSerializer
    
    def get_queryset(self):
        return TrainerSession.objects.filter(
            trainer=self.request.user
        ).select_related('member__user').order_by('-session_date', '-start_time')
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant, 
            trainer=self.request.user
        )


class TrainerLeaveRequestViewSet(viewsets.ModelViewSet):
    """Trainer leave request management"""
    permission_classes = [IsAuthenticated, IsTrainer]
    serializer_class = LeaveRequestSerializer
    
    def get_queryset(self):
        queryset = LeaveRequest.objects.all().select_related('member__user').order_by('-created_at')
        if self.request.tenant:
            queryset = queryset.filter(tenant=self.request.tenant)
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve leave request"""
        leave_request = self.get_object()
        leave_request.status = 'Approved'
        leave_request.approved_by = request.user
        leave_request.save()
        
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject leave request"""
        leave_request = self.get_object()
        leave_request.status = 'Rejected'
        leave_request.approved_by = request.user
        leave_request.save()
        
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)


class TrainerDietPlanViewSet(viewsets.ModelViewSet):
    """Trainer diet plan management"""
    permission_classes = [IsAuthenticated, IsTrainer]
    serializer_class = DietPlanSerializer
    
    def get_queryset(self):
        queryset = DietPlan.objects.all().select_related('member__user', 'assigned_by').order_by('-created_at')
        if self.request.tenant:
            queryset = queryset.filter(tenant=self.request.tenant)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant,
            assigned_by=self.request.user
        )
