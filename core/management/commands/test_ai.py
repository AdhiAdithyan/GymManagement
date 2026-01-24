from django.core.management.base import BaseCommand
from django.conf import settings
from gym.ai_service import GeminiAIService
from core.models import MemberProfile
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Test AI Service Generation'

    def handle(self, *args, **kwargs):
        self.stdout.write("Testing AI Service...")

        if not settings.GEMINI_API_KEY:
            self.stdout.write(self.style.WARNING("GEMINI_API_KEY not found in settings. AI services will use fallback/mock data or fail."))
            
        # Get a dummy member or create one
        user = User.objects.first()
        if not user:
            self.stdout.write("No users found. Creating test user.")
            user = User.objects.create_user(username='test_ai_user', password='password123')
            
        try:
            member = user.member_profile
        except MemberProfile.DoesNotExist:
             self.stdout.write("Creating MemberProfile for test user...")
             member = MemberProfile.objects.create(
                user=user,
                membership_type='monthly',
                age=30,
                registration_amount=100.00,
                monthly_amount=50.00,
                allotted_slot="6:00 AM - 7:00 AM"
            )

        service = GeminiAIService()
        
        # Test Workout Generation
        self.stdout.write("1. Testing Workout Plan Generation...")
        workout_result = service.generate_workout_plan(
            member_profile=member,
            goals="Build Muscle",
            duration_weeks=4,
            days_per_week=3
        )
        
        if workout_result.get('success'):
            self.stdout.write(self.style.SUCCESS("[OK] Workout Plan Generated Successfully"))
        elif 'fallback_plan' in workout_result:
             self.stdout.write(self.style.WARNING(f"[WARN] Workout Gen Failed, used Fallback: {workout_result.get('error')}"))
        else:
             self.stdout.write(self.style.ERROR(f"[X] Workout Plan Generation Failed: {workout_result.get('error')}"))

        # Test Diet Generation
        self.stdout.write("\n2. Testing Diet Plan Generation...")
        diet_result = service.generate_diet_plan(
            member_profile=member,
            goals="Weight Loss",
            dietary_restrictions=["Vegetarian"]
        )
        
        if diet_result.get('success'):
             self.stdout.write(self.style.SUCCESS("[OK] Diet Plan Generated Successfully"))
        elif 'fallback_plan' in diet_result:
             self.stdout.write(self.style.WARNING(f"[WARN] Diet Gen Failed, used Fallback: {diet_result.get('error')}"))
        else:
             self.stdout.write(self.style.ERROR(f"[X] Diet Plan Generation Failed: {diet_result.get('error')}"))
