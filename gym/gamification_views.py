from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Max
from core.gamification_models import (
    Exercise, WorkoutLog, PersonalBest, Achievement, 
    Leaderboard, Challenge, ChallengeParticipation
)
from gym.analytics_service import AnalyticsService

@login_required
def gamification_dashboard(request):
    """Main dashboard for gamification features"""
    member = request.user.member_profile
    
    # Get recent logs
    recent_logs = WorkoutLog.objects.filter(member=member).order_by('-logged_at')[:5]
    
    # Get personal bests
    pbs = PersonalBest.objects.filter(member=member).order_by('-achieved_at')[:3]
    
    # Get recent achievements
    achievements = Achievement.objects.filter(member=member).order_by('-earned_at')[:3]
    
    # Get points/level (simplified for now)
    exercises_completed = WorkoutLog.objects.filter(member=member).count()
    level = int(exercises_completed / 10) + 1
    
    return render(request, 'gym/gamification_dashboard.html', {
        'recent_logs': recent_logs,
        'pbs': pbs,
        'achievements': achievements,
        'level': level,
        'points': exercises_completed * 50
    })

@login_required
def log_workout(request):
    """
    View to log a workout. Supports both standard POST and HTMX.
    """
    exercises = Exercise.objects.all().order_by('name')
    
    if request.method == 'POST':
        exercise_id = request.POST.get('exercise')
        sets = request.POST.get('sets')
        reps = request.POST.get('reps')
        weight = request.POST.get('weight')
        duration = request.POST.get('duration')
        
        try:
            exercise = Exercise.objects.get(id=exercise_id)
            
            # Create log
            log = WorkoutLog.objects.create(
                member=request.user.member_profile,
                exercise=exercise,
                sets=int(sets) if sets else None,
                reps=int(reps) if reps else None,
                weight=float(weight) if weight else None,
                duration_seconds=int(duration) * 60 if duration else None,
                notes=request.POST.get('notes', ''),
                logged_at=timezone.now()
            )
            
            # Update Engagement Score (trigger update to keep it fresh)
            AnalyticsService.calculate_engagement_score(request.user.member_profile)
            
            # Check for Personal Best
            if weight and exercise.measurement_type == 'weight':
                current_pb = PersonalBest.objects.filter(
                    member=request.user.member_profile,
                    exercise=exercise
                ).first()
                
                if not current_pb or float(weight) > current_pb.value:
                    PersonalBest.objects.update_or_create(
                        member=request.user.member_profile,
                        exercise=exercise,
                        defaults={
                            'value': float(weight),
                            'achieved_at': timezone.now()
                        }
                    )
                    messages.success(request, f"New Personal Best! {weight}kg on {exercise.name}")
            
            if request.htmx:
                # Return partial for HTMX
                recent_logs = WorkoutLog.objects.filter(
                    member=request.user.member_profile
                ).order_by('-logged_at')[:5]
                
                return render(request, 'gym/partials/workout_history_list.html', {
                    'logs': recent_logs
                })
                
            messages.success(request, "Workout logged successfully!")
            return redirect('log_workout')
            
        except Exception as e:
            if request.htmx:
                return HttpResponse(f"<div class='alert alert-danger'>Error: {str(e)}</div>")
            messages.error(request, f"Error logging workout: {str(e)}")
    
    # GET request
    recent_logs = WorkoutLog.objects.filter(
        member=request.user.member_profile
    ).order_by('-logged_at')[:10]
    
    return render(request, 'gym/log_workout.html', {
        'exercises': exercises,
        'logs': recent_logs
    })

@login_required
def leaderboard(request):
    """Global leaderboard view"""
    # Simply count workouts for now as 'points'
    # In a real app, this would be more complex
    
    leaders = WorkoutLog.objects.values('member__user__username', 'member__user__first_name', 'member__user__last_name') \
        .annotate(total_workouts=Count('id')) \
        .order_by('-total_workouts')[:10]
        
    return render(request, 'gym/leaderboard.html', {
        'leaders': leaders
    })

@login_required
def achievements_view(request):
    """View member achievements"""
    # Logic to check and award new achievements could go here
    # For now, just display existing ones
    
    my_achievements = Achievement.objects.filter(member=request.user.member_profile)
    
    # Define some available badges (mock data for display)
    available_badges = [
        {'name': 'First Step', 'description': 'Log your first workout', 'icon': '🦶'},
        {'name': 'Consistency King', 'description': 'Work out 3 days in a row', 'icon': '👑'},
        {'name': 'Heavy Lifter', 'description': 'Bench press 100kg', 'icon': '🏋️'},
    ]
    
    return render(request, 'gym/achievements.html', {
        'achievements': my_achievements,
        'available_badges': available_badges
    })
