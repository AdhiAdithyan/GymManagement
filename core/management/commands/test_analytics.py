from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import MemberProfile, Attendance, Payment
from django.contrib.auth import get_user_model
from core.gamification_models import WorkoutLog, Exercise
from gym.analytics_service import AnalyticsService

User = get_user_model()

class Command(BaseCommand):
    help = 'Test Analytics Service and Engagement Score'

    def handle(self, *args, **kwargs):
        self.stdout.write("Testing Analytics Service...")
        
        # Get or create a test user for analytics
        user_ids = MemberProfile.objects.values_list('user_id', flat=True)
        if not user_ids:
             self.stdout.write(self.style.ERROR("No users found. Creating a test user."))
             user = User.objects.create_user(username='test_analytics_user', password='password123')
        else:
            user = User.objects.get(id=user_ids[0])
             
        try:
            member = user.member_profile
        except MemberProfile.DoesNotExist:
            self.stdout.write("Creating MemberProfile for test user...")
            member = MemberProfile.objects.create(
                user=user,
                membership_type='monthly',
                age=25,
                registration_amount=100.00,
                monthly_amount=50.00,
                allotted_slot="6:00 AM - 7:00 AM"
            )

        self.stdout.write(f"Testing with member: {member.user.username}")
        
        # 1. Simulate some data to allow score calculation
        # Add recent attendance
        Attendance.objects.create(
            member=member,
            date=(timezone.now() - timedelta(days=1)).date(),
            check_in_time=(timezone.now() - timedelta(days=1)).time(),
            status='present'
        )
        Attendance.objects.create(
            member=member,
            date=(timezone.now() - timedelta(days=3)).date(),
            check_in_time=(timezone.now() - timedelta(days=3)).time(),
            status='present'
        )
        self.stdout.write("[OK] Added mock attendance records")
        
        # Add a workout log
        exercise = Exercise.objects.first()
        if exercise:
            WorkoutLog.objects.create(
                member=member,
                exercise=exercise,
                sets=3,
                reps=10,
                value=50.0, # Added value (weight/time/etc)
                logged_at=timezone.now() - timedelta(hours=2)
            )
            self.stdout.write("[OK] Added mock workout log")

        # 2. Calculate Engagement Score
        self.stdout.write("\nCalculating Engagement Score...")
        score = AnalyticsService.calculate_engagement_score(member)
        churn_risk = AnalyticsService.predict_churn_risk(member)
        
        self.stdout.write("  - Score: " + str(score))
        self.stdout.write("  - Level: " + str(churn_risk))
        
        if score > 0:
            self.stdout.write(self.style.SUCCESS("[OK] Engagement Score calculation works (Score > 0)"))
        else:
            self.stdout.write(self.style.WARNING("[WARN] Score is 0. Check scoring logic if this is unexpected."))

        # 3. Test Gym Analytics
        self.stdout.write("\nFetching Gym-wide Analytics...")
        stats = AnalyticsService.get_gym_analytics(member.tenant)
        self.stdout.write(f"  - Total Members: {stats['members']['total']}")
        self.stdout.write(f"  - Avg Engagement: {stats['engagement']['average_score']}")
        
        if stats:
            self.stdout.write(self.style.SUCCESS("[OK] Gym Analytics retrieval successful"))
