from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Create router for viewsets
router = DefaultRouter()

# Member endpoints
router.register(r'member/attendance', views.MemberAttendanceViewSet, basename='member-attendance')
router.register(r'member/payments', views.MemberPaymentViewSet, basename='member-payments')
router.register(r'member/diet-plans', views.MemberDietPlanViewSet, basename='member-diet-plans')
router.register(r'member/videos', views.MemberWorkoutVideoViewSet, basename='member-videos')
router.register(r'member/leave-requests', views.MemberLeaveRequestViewSet, basename='member-leave-requests')

# Trainer endpoints
router.register(r'trainer/members', views.TrainerMemberViewSet, basename='trainer-members')
router.register(r'trainer/attendance', views.TrainerAttendanceViewSet, basename='trainer-attendance')
router.register(r'trainer/sessions', views.TrainerSessionViewSet, basename='trainer-sessions')
router.register(r'trainer/leave-requests', views.TrainerLeaveRequestViewSet, basename='trainer-leave-requests')
router.register(r'trainer/diet-plans', views.TrainerDietPlanViewSet, basename='trainer-diet-plans')

urlpatterns = [
    # Authentication
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Branding
    path('branding/', views.get_branding, name='branding'),
    
    # Member custom endpoints
    path('member/dashboard/', views.member_dashboard, name='member-dashboard'),
    path('member/check-in/', views.member_check_in, name='member-checkin'),
    
    # Trainer custom endpoints
    path('trainer/dashboard/', views.trainer_dashboard, name='trainer-dashboard'),
    
    # All router URLs
    path('', include(router.urls)),
]
