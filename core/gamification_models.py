"""
Gamification Models for Member Engagement
Includes workout logging, personal bests, achievements, and leaderboards
"""
from django.db import models
from django.utils import timezone
from .models import Tenant, MemberProfile


class Exercise(models.Model):
    """Exercise database"""
    CATEGORY_CHOICES = (
        ('strength', 'Strength Training'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility & Mobility'),
        ('sports', 'Sports'),
        ('other', 'Other'),
    )
    
    MEASUREMENT_CHOICES = (
        ('weight', 'Weight (kg)'),
        ('reps', 'Repetitions'),
        ('time', 'Time (seconds)'),
        ('distance', 'Distance (meters)'),
        ('calories', 'Calories'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    measurement_type = models.CharField(max_length=20, choices=MEASUREMENT_CHOICES)
    
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True, help_text="How to perform the exercise")
    
    # Metadata
    muscle_groups = models.JSONField(default=list, help_text="List of muscle groups targeted")
    difficulty_level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], default='intermediate')
    
    equipment_required = models.CharField(max_length=200, blank=True)
    video_url = models.URLField(blank=True, help_text="YouTube or instructional video URL")
    image = models.ImageField(upload_to='exercises/', null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exercises'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class WorkoutLog(models.Model):
    """Individual workout entries by members"""
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='workout_logs')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='logs')
    
    # Workout details
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Primary measurement value")
    sets = models.IntegerField(null=True, blank=True)
    reps = models.IntegerField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    distance_meters = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    difficulty_rating = models.IntegerField(null=True, blank=True, help_text="1-5, how hard was it")
    
    # Tracking
    is_personal_best = models.BooleanField(default=False)
    logged_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'workout_logs'
        ordering = ['-logged_at']
        indexes = [
            models.Index(fields=['member', 'exercise']),
            models.Index(fields=['logged_at']),
            models.Index(fields=['is_personal_best']),
        ]
    
    def __str__(self):
        return f"{self.member.user.username} - {self.exercise.name} - {self.value}"
    
    def save(self, *args, **kwargs):
        """Check if this is a personal best"""
        if self.pk is None:  # New log
            previous_best = PersonalBest.objects.filter(
                member=self.member,
                exercise=self.exercise
            ).first()
            
            if previous_best:
                if self.value > previous_best.best_value:
                    self.is_personal_best = True
                    # Update personal best
                    previous_best.previous_best = previous_best.best_value
                    previous_best.best_value = self.value
                    previous_best.achieved_date = self.logged_at.date()
                    previous_best.save()
            else:
                # First time logging this exercise
                self.is_personal_best = True
                PersonalBest.objects.create(
                    member=self.member,
                    exercise=self.exercise,
                    best_value=self.value,
                    achieved_date=self.logged_at.date()
                )
        
        super().save(*args, **kwargs)


class PersonalBest(models.Model):
    """Track personal bests for each exercise"""
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='personal_bests')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='personal_bests')
    
    best_value = models.DecimalField(max_digits=10, decimal_places=2)
    previous_best = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    achieved_date = models.DateField()
    times_improved = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'personal_bests'
        unique_together = ['member', 'exercise']
        ordering = ['-achieved_date']
    
    def __str__(self):
        return f"{self.member.user.username} - {self.exercise.name} PB: {self.best_value}"


class Achievement(models.Model):
    """Badges and achievements earned by members"""
    ACHIEVEMENT_TYPES = (
        # Attendance based
        ('attendance_7_day', '7 Day Streak'),
        ('attendance_30_day', '30 Day Streak'),
        ('attendance_100_day', '100 Day Streak'),
        ('attendance_365_day', '365 Day Streak'),
        
        # Workout based
        ('first_workout', 'First Workout Logged'),
        ('workouts_10', '10 Workouts Logged'),
        ('workouts_50', '50 Workouts Logged'),
        ('workouts_100', '100 Workouts Logged'),
        
        # Personal Best based
        ('first_pb', 'First Personal Best'),
        ('pb_5', '5 Personal Bests'),
        ('pb_10', '10 Personal Bests'),
        ('pb_broken', 'PB Broken'),
        
        # Membership based
        ('member_1_month', '1 Month Member'),
        ('member_6_months', '6 Months Member'),
        ('member_1_year', '1 Year Member'),
        ('member_2_years', '2 Years Member'),
        
        # Social based
        ('referral_1', 'First Referral'),
        ('referral_5', '5 Referrals'),
        
        # Special
        ('early_bird', 'Early Bird (6 AM Check-in)'),
        ('night_owl', 'Night Owl (9 PM Check-in)'),
        ('weekend_warrior', 'Weekend Warrior'),
    )
    
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES)
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Icon identifier (emoji or icon class)")
    
    earned_at = models.DateTimeField(default=timezone.now)
    
    # Points system
    points = models.IntegerField(default=10)
    
    class Meta:
        db_table = 'achievements'
        unique_together = ['member', 'achievement_type']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['member', 'earned_at']),
        ]
    
    def __str__(self):
        return f"{self.member.user.username} - {self.title}"


class MemberEngagementScore(models.Model):
    """Calculate and track member engagement metrics"""
    CHURN_RISK_CHOICES = (
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    )
    
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='engagement_scores')
    
    # Engagement metrics (0-100 scale)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Overall engagement score 0-100")
    attendance_score = models.DecimalField(max_digits=5, decimal_places=2)
    workout_logging_score = models.DecimalField(max_digits=5, decimal_places=2)
    payment_score = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Attendance metrics
    attendance_rate_30d = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage")
    last_visit_days_ago = models.IntegerField()
    current_streak_days = models.IntegerField(default=0)
    longest_streak_days = models.IntegerField(default=0)
    
    # Payment status
    payment_status = models.CharField(max_length=20, choices=[
        ('current', 'Current'),
        ('due', 'Payment Due'),
        ('overdue', 'Overdue'),
        ('suspended', 'Suspended'),
    ])
    days_until_payment_due = models.IntegerField(null=True, blank=True)
    
    # Churn prediction
    churn_risk = models.CharField(max_length=20, choices=CHURN_RISK_CHOICES)
    churn_probability = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage 0-100")
    
    # Recommendations
    recommended_actions = models.JSONField(default=list, help_text="List of recommended retention actions")
    
    calculated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'member_engagement_scores'
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['member', 'calculated_at']),
            models.Index(fields=['churn_risk']),
        ]
    
    def __str__(self):
        return f"{self.member.user.username} - Score: {self.overall_score} - Risk: {self.churn_risk}"


class Leaderboard(models.Model):
    """Leaderboard entries for various metrics"""
    LEADERBOARD_TYPES = (
        ('attendance_month', 'Monthly Attendance'),
        ('attendance_all_time', 'All-Time Attendance'),
        ('workouts_month', 'Monthly Workouts'),
        ('workouts_all_time', 'All-Time Workouts'),
        ('pbs_month', 'Monthly Personal Bests'),
        ('pbs_all_time', 'All-Time Personal Bests'),
        ('points_month', 'Monthly Points'),
        ('points_all_time', 'All-Time Points'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='leaderboards')
    leaderboard_type = models.CharField(max_length=50, choices=LEADERBOARD_TYPES)
    
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='leaderboard_entries')
    rank = models.IntegerField()
    score = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Time period
    period_start = models.DateField()
    period_end = models.DateField()
    
    calculated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'leaderboards'
        unique_together = ['leaderboard_type', 'member', 'period_start', 'period_end']
        ordering = ['leaderboard_type', 'rank']
        indexes = [
            models.Index(fields=['tenant', 'leaderboard_type', 'period_start']),
            models.Index(fields=['member', 'leaderboard_type']),
        ]
    
    def __str__(self):
        return f"{self.get_leaderboard_type_display()} - Rank {self.rank}: {self.member.user.username}"


class Challenge(models.Model):
    """Gym challenges for member engagement"""
    STATUS_CHOICES = (
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='challenges')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    challenge_type = models.CharField(max_length=50, choices=[
        ('attendance', 'Attendance Challenge'),
        ('workout_count', 'Workout Count'),
        ('specific_exercise', 'Specific Exercise'),
        ('team', 'Team Challenge'),
    ])
    
    # Challenge parameters
    target_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Target to achieve")
    target_exercise = models.ForeignKey(Exercise, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    # Rewards
    reward_points = models.IntegerField(default=100)
    reward_description = models.TextField(blank=True)
    
    # Participation
    participants = models.ManyToManyField(MemberProfile, through='ChallengeParticipation', related_name='challenges')
    
    image = models.ImageField(upload_to='challenges/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'challenges'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} ({self.status})"


class ChallengeParticipation(models.Model):
    """Track member participation in challenges"""
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='participations')
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='challenge_participations')
    
    joined_at = models.DateTimeField(default=timezone.now)
    
    # Progress tracking
    current_progress = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Completion
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Ranking within challenge
    rank = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'challenge_participations'
        unique_together = ['challenge', 'member']
        ordering = ['-current_progress']
    
    def __str__(self):
        return f"{self.member.user.username} - {self.challenge.title} ({self.progress_percentage}%)"
