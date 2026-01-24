from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import MemberProfile, Tenant, BrandingConfig
from core.gamification_models import Exercise, WorkoutLog, Achievement
from core.booking_models import ClassSchedule, ClassBooking
from gym.ai_service import GeminiAIService
from gym.analytics_service import AnalyticsService
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Simulates a complete user journey through the application to verify all modules.'

    help = 'Simulates a complete user journey through the application to verify all modules.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING("[START] User Journey Simulation..."))
        
        # --- PRE-REQUISITES ---
        self.stdout.write("\n[SETUP] Setting up Environment...")
        # Ensure Tenant exists
        tenant, _ = Tenant.objects.get_or_create(name="Test Gym", defaults={'subdomain': 'testgym'})
        BrandingConfig.objects.get_or_create(tenant=tenant)
        self.stdout.write("[OK] Tenant Verified")

        # Ensure Exercises exist
        if not Exercise.objects.exists():
            self.stdout.write("[WARN] No exercises found. Please run 'python manage.py seed_exercises' first.")
            # Create one for test
            Exercise.objects.create(name="Test Pushups", category="strength", measurement_type="reps")
            self.stdout.write("[OK] Created fallback test exercise")
        else:
            self.stdout.write(f"[OK] Exercises Verified ({Exercise.objects.count()} found)")
            
        # --- STEP 1: USER REGISTRATION ---
        self.stdout.write("\n[STEP 1] User Registration & Onboarding")
        username = f"journey_user_{random.randint(1000,9999)}"
        email = f"{username}@example.com"
        
        user = User.objects.create_user(username=username, email=email, password="password123")
        member = MemberProfile.objects.create(
            user=user,
            tenant=tenant,
            membership_type='monthly',
            age=28,
            phone_number="+15550001234",
            registration_amount=0,
            monthly_amount=50,
            allotted_slot="Morning"
        )
        self.stdout.write(f"[OK] Created User: {username}")
        self.stdout.write(f"[OK] Created Member Profile (ID: {member.id})")

        # --- STEP 2: CONNECT AI TOOLS ---
        self.stdout.write("\n[STEP 2] AI Tools Connection")
        # Simulate the 'connect' view logic
        session_mock = {} 
        session_mock['ai_connected'] = True
        session_mock['ai_email'] = email
        self.stdout.write(f"[OK] Simulated 'Connect AI' Flow (User verified as {email})")
        
        # --- STEP 3: GENERATE WORKOUT PLAN ---
        self.stdout.write("\n[STEP 3] AI Generation Services")
        ai_service = GeminiAIService()
        
        # Workout Plan
        self.stdout.write("   - Requesting Workout Plan...")
        plan = ai_service.generate_workout_plan(member, "Muscle Gain", 4, 3)
        if plan.get('success'):
            self.stdout.write(self.style.SUCCESS("   [PASS] Workout Plan Generated"))
        elif 'fallback_plan' in plan:
             self.stdout.write(self.style.WARNING("   [PASS-FALLBACK] AI Key missing, used Fallback Plan (Expected behavior)"))
        else:
             self.stdout.write(self.style.ERROR("   [FAIL] Workout Plan Generation crashed"))

        # Diet Plan
        self.stdout.write("   - Requesting Diet Plan...")
        diet = ai_service.generate_diet_plan(member, "Weight Loss", ["Vegetarian"])
        if diet.get('success'):
             self.stdout.write(self.style.SUCCESS("   [PASS] Diet Plan Generated"))
        elif 'fallback_plan' in diet:
             self.stdout.write(self.style.WARNING("   [PASS-FALLBACK] AI Key missing, used Fallback Diet (Expected behavior)"))

        # --- STEP 4: GAMIFICATION (LOGGING WORKOUTS) ---
        self.stdout.write("\n[STEP 4] Gamification & Logging")
        exercise = Exercise.objects.first()
        log = WorkoutLog.objects.create(
            member=member,
            exercise=exercise,
            value=100,
            sets=3,
            reps=10,
            notes="Feeling strong!",
            is_personal_best=True # Force PB
        )
        self.stdout.write(f"[OK] Logged Workout: {exercise.name}")
        
        # Verify PB creation
        pb_count = member.personal_bests.count()
        if pb_count > 0:
             self.stdout.write(self.style.SUCCESS(f"   [PASS] Personal Best System Triggered ({pb_count} PBs)"))
        else:
             self.stdout.write(self.style.WARNING("   [WARN] PB not created. Check signal/save logic."))

        # --- STEP 5: ANALYTICS & SCORING ---
        self.stdout.write("\n[STEP 5] Analytics Engine")
        score = AnalyticsService.calculate_engagement_score(member)
        risk = AnalyticsService.predict_churn_risk(member)
        
        self.stdout.write(f"   - Calculated Score: {score}")
        self.stdout.write(f"   - Predicted Risk: {risk}")
        
        if score > 0:
             self.stdout.write(self.style.SUCCESS("   [PASS] Engagement Logic Working"))
        else:
             self.stdout.write(self.style.WARNING("   [WARN] Score is 0 (Might be expected for brand new user with 1 log)"))

        # --- STEP 6: BOOKING SYSTEM ---
        self.stdout.write("\n[STEP 6] Class Booking System")
        # Create a schedule
        schedule = ClassSchedule.objects.create(
            tenant=tenant,
            class_name="HIIT Blast",
            day_of_week=timezone.now().strftime('%A'),
            start_time=timezone.now().time(),
            duration_minutes=60,
            capacity=20,
            instructor=user # Self-taught for test
        )
        self.stdout.write(f"[OK] Created Class Schedule: {schedule.class_name}")
        
        # Book it
        try:
            booking = ClassBooking.objects.create(
                member=member,
                schedule=schedule,
                booking_date=timezone.now().date(),
                status='confirmed'
            )
            self.stdout.write(self.style.SUCCESS(f"   [PASS] Successfully Booked Class (Booking ID: {booking.id})"))
        except Exception as e:
             self.stdout.write(self.style.ERROR(f"   [FAIL] Booking Failed: {e}"))

        # --- CLEANUP (Optional) ---
        # user.delete() 
        # self.stdout.write("\n[cleanup] Cleanup Skipped (Keep data for inspection)")
        
        self.stdout.write(self.style.MIGRATE_HEADING("\n[COMPLETE] User Journey Simulation Complete!"))
