"""
Analytics Service
Handles churn prediction and engagement analytics
"""
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import timedelta
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from core.models import MemberProfile, Attendance
from core.gamification_models import WorkoutLog, MemberEngagementScore
from core.payment_models import SubscriptionPayment


class AnalyticsService:
    """Analytics and churn prediction service"""
    
    @staticmethod
    def calculate_engagement_score(member):
        """
        Calculate comprehensive engagement score (0-100)
        
        Factors:
        - Attendance frequency (30%)
        - Payment history (20%)
        - Workout logging (25%)
        - Last visit recency (15%)
        - Achievements (10%)
        """
        score = 0
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # 1. Attendance Score (30 points)
        attendance_count = Attendance.objects.filter(
            member=member,
            date__gte=thirty_days_ago.date()
        ).count()
        
        # Expected: 12 visits per month (3x/week)
        attendance_score = min((attendance_count / 12) * 30, 30)
        score += attendance_score
        
        # 2. Payment Score (20 points)
        recent_payments = SubscriptionPayment.objects.filter(
            member=member,
            payment_date__gte=thirty_days_ago,
            status='completed'
        ).count()
        
        payment_score = min(recent_payments * 20, 20)
        score += payment_score
        
        # 3. Workout Logging Score (25 points)
        workout_logs = WorkoutLog.objects.filter(
            member=member,
            logged_at__gte=thirty_days_ago
        ).count()
        
        # Expected: 12 logs per month
        workout_score = min((workout_logs / 12) * 25, 25)
        score += workout_score
        
        # 4. Recency Score (15 points)
        last_visit = Attendance.objects.filter(member=member).order_by('-date', '-check_in_time').first()
        if last_visit:
            days_since_visit = (now.date() - last_visit.date).days
            if days_since_visit <= 3:
                recency_score = 15
            elif days_since_visit <= 7:
                recency_score = 10
            elif days_since_visit <= 14:
                recency_score = 5
            else:
                recency_score = 0
            score += recency_score
        
        # 5. Achievement Score (10 points)
        from core.gamification_models import Achievement
        achievements_count = Achievement.objects.filter(
            member=member,
            earned_at__gte=thirty_days_ago
        ).count()
        
        achievement_score = min(achievements_count * 2, 10)
        score += achievement_score
        
        return round(score, 2)
    
    @staticmethod
    def predict_churn_risk(member):
        """
        Predict churn risk based on engagement patterns
        
        Returns:
            str: 'low', 'medium', 'high', 'critical'
        """
        engagement_score = AnalyticsService.calculate_engagement_score(member)
        
        # Get additional factors
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Check last visit
        last_visit = Attendance.objects.filter(member=member).order_by('-date', '-check_in_time').first()
        days_since_visit = (now.date() - last_visit.date).days if last_visit else 999
        
        # Check payment status
        overdue_payments = SubscriptionPayment.objects.filter(
            member=member,
            status='failed'
        ).count()
        
        # Churn risk logic
        if engagement_score >= 70 and days_since_visit <= 7:
            return 'low'
        elif engagement_score >= 50 and days_since_visit <= 14:
            return 'medium'
        elif engagement_score >= 30 or days_since_visit <= 21:
            return 'high'
        else:
            return 'critical'
    
    @staticmethod
    def get_member_insights(member):
        """Get comprehensive member insights"""
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        ninety_days_ago = now - timedelta(days=90)
        
        # Attendance insights
        attendance_30d = Attendance.objects.filter(
            member=member,
            date__gte=thirty_days_ago.date()
        ).count()
        
        attendance_90d = Attendance.objects.filter(
            member=member,
            date__gte=ninety_days_ago.date()
        ).count()
        
        # Workout insights
        workouts_30d = WorkoutLog.objects.filter(
            member=member,
            logged_at__gte=thirty_days_ago
        ).count()
        
        personal_bests = WorkoutLog.objects.filter(
            member=member,
            is_personal_best=True
        ).count()
        
        # Payment insights
        total_paid = SubscriptionPayment.objects.filter(
            member=member,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Engagement score
        engagement_score = AnalyticsService.calculate_engagement_score(member)
        churn_risk = AnalyticsService.predict_churn_risk(member)
        
        return {
            'engagement_score': engagement_score,
            'churn_risk': churn_risk,
            'attendance': {
                'last_30_days': attendance_30d,
                'last_90_days': attendance_90d,
                'average_per_week': round(attendance_30d / 4.3, 1)
            },
            'workouts': {
                'last_30_days': workouts_30d,
                'personal_bests': personal_bests
            },
            'financial': {
                'total_paid': float(total_paid),
                'lifetime_value': float(total_paid)
            }
        }
    
    @staticmethod
    def get_gym_analytics(tenant):
        """Get gym-wide analytics"""
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Member stats
        total_members = MemberProfile.objects.filter(tenant=tenant).count()
        active_members = Attendance.objects.filter(
            member__tenant=tenant,

            date__gte=thirty_days_ago.date()
        ).values('member').distinct().count()
        
        # Revenue stats
        revenue_30d = SubscriptionPayment.objects.filter(
            member__tenant=tenant,
            payment_date__gte=thirty_days_ago,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Engagement stats
        avg_engagement = MemberEngagementScore.objects.filter(
            member__tenant=tenant
        ).aggregate(avg=Avg('overall_score'))['avg'] or 0
        
        # Churn risk distribution
        churn_distribution = MemberEngagementScore.objects.filter(
            member__tenant=tenant
        ).values('churn_risk').annotate(count=Count('id'))
        
        return {
            'members': {
                'total': total_members,
                'active_30d': active_members,
                'retention_rate': round((active_members / total_members * 100) if total_members > 0 else 0, 2)
            },
            'revenue': {
                'last_30_days': float(revenue_30d),
                'average_per_member': float(revenue_30d / total_members) if total_members > 0 else 0
            },
            'engagement': {
                'average_score': round(avg_engagement, 2),
                'churn_distribution': list(churn_distribution)
            }
        }
    
    @staticmethod
    def update_all_engagement_scores(tenant):
        """Update engagement scores for all members"""
        members = MemberProfile.objects.filter(tenant=tenant)
        updated_count = 0
        
        for member in members:
            score = AnalyticsService.calculate_engagement_score(member)
            churn_risk = AnalyticsService.predict_churn_risk(member)
            
            # Get last visit
            # Get last visit
            last_visit = Attendance.objects.filter(member=member).order_by('-date', '-check_in_time').first()
            days_since_visit = (timezone.now().date() - last_visit.date).days if last_visit else 999
            
            # Check payment status
            has_overdue = SubscriptionPayment.objects.filter(
                member=member,
                status='failed'
            ).exists()
            
            # Update or create engagement score
            MemberEngagementScore.objects.update_or_create(
                member=member,
                defaults={
                    'overall_score': score,
                    'attendance_score': min((Attendance.objects.filter(
                        member=member,
                        date__gte=(timezone.now() - timedelta(days=30)).date()
                    ).count() / 12) * 30, 30),
                    'workout_score': min((WorkoutLog.objects.filter(
                        member=member,
                        logged_at__gte=timezone.now() - timedelta(days=30)
                    ).count() / 12) * 25, 25),
                    'payment_score': 20 if not has_overdue else 0,
                    'last_visit_days_ago': days_since_visit,
                    'churn_risk': churn_risk,
                    'payment_status': 'current' if not has_overdue else 'overdue',
                    'calculated_at': timezone.now()
                }
            )
            updated_count += 1
        
        return updated_count


# Convenience functions
def get_member_analytics(member):
    """Quick function to get member analytics"""
    return AnalyticsService.get_member_insights(member)


def update_engagement_scores(tenant):
    """Quick function to update all engagement scores"""
    return AnalyticsService.update_all_engagement_scores(tenant)


def get_gym_dashboard_data(tenant):
    """Quick function to get gym analytics"""
    return AnalyticsService.get_gym_analytics(tenant)
