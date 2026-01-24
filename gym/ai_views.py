from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .ai_service import GeminiAIService
from .analytics_service import AnalyticsService
from django.contrib.auth.models import User
from django.conf import settings
import json
import markdown

@login_required
def connect_ai_tools(request):
    """
    View to let users 'connect' their AI tools by providing email/phone.
    This simulates an authentication flow requested by the user.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        # Save this 'connection' - for now we'll mark it in session
        # In a real app, we might store this in a dedicated model or the MemberProfile
        request.session['ai_connected'] = True
        request.session['ai_email'] = email
        request.session['ai_phone'] = phone
        
        # Also update the profile if it exists
        try:
            profile = request.user.member_profile
            if phone and not profile.phone_number:
                profile.phone_number = phone
                profile.save()
        except:
            pass
            
        messages.success(request, "AI Assistant successfully connected!")
        
        # Redirect back to where they came from or default
        next_url = request.GET.get('next', 'dashboard')
        return redirect(next_url)
        
    return render(request, 'gym/connect_ai_tools.html')

from django.urls import reverse

@login_required
def ai_workout_plan(request):
    """
    View to handle AI workout plan generation.
    Checks if user is 'connected' first.
    """
    # Check connection status
    if not request.session.get('ai_connected'):
        # Pass name of view to reverse
        return redirect(f"{reverse('connect_ai_tools')}?next=ai_workout_plan")

    if request.method == 'POST':
        goal = request.POST.get('goal')
        fitness_level = request.POST.get('fitness_level')
        duration = int(request.POST.get('duration', 4))
        days_per_week = int(request.POST.get('days_per_week', 3))
        
        # Initialize AI Service
        ai_service = GeminiAIService()
        
        try:
            # Generate the plan
            plan_data = ai_service.generate_workout_plan(
                member_profile=request.user.member_profile,
                goals=goal,
                duration_weeks=duration,
                days_per_week=days_per_week
            )
            
            request.session['generated_workout_plan'] = plan_data
            messages.success(request, "Your AI-powered workout plan has been generated!")
            return redirect('view_workout_plan')
            
        except Exception as e:
            messages.error(request, f"Failed to generate plan: {str(e)}")
            return redirect('ai_workout_plan')

    # We removed 'api_key_configured' check to rely on the 'connect' flow and fallback
    return render(request, 'gym/ai_workout_plan.html', {
        'api_key_configured': True # Always allow if they passed the connect screen
    })

@login_required
def view_workout_plan(request):
    """
    Display the generated workout plan.
    """
    plan_data = request.session.get('generated_workout_plan')
    
    if not plan_data:
        messages.warning(request, "No workout plan found. Please generate one first.")
        return redirect('ai_workout_plan')
    
    # Extract the actual plan dictionary
    if plan_data.get('success'):
        workout_plan = plan_data.get('plan')
    else:
        # If failed, use fallback plan if available
        workout_plan = plan_data.get('fallback_plan')
        if not workout_plan:
             workout_plan = {}
    
    return render(request, 'gym/view_workout_plan.html', {
        'plan': workout_plan
    })

@login_required
def ai_diet_plan(request):
    """
    View to handle AI diet plan generation.
    Checks if user is 'connected' first.
    """
    # Check connection status
    if not request.session.get('ai_connected'):
        return redirect(f"{reverse('connect_ai_tools')}?next=ai_diet_plan")

    if request.method == 'POST':
        goal = request.POST.get('goal')
        dietary_restrictions = request.POST.getlist('dietary_restrictions')
        
        # Initialize AI Service
        ai_service = GeminiAIService()
        
        try:
            # Generate the plan
            plan_data = ai_service.generate_diet_plan(
                member_profile=request.user.member_profile,
                goals=goal,
                dietary_restrictions=dietary_restrictions
            )
            
            request.session['generated_diet_plan'] = plan_data
            messages.success(request, "Your AI-powered diet plan has been generated!")
            return redirect('view_diet_plan')
            
        except Exception as e:
            messages.error(request, f"Failed to generate plan: {str(e)}")
            return redirect('ai_diet_plan')

    return render(request, 'gym/ai_diet_plan.html', {
        'api_key_configured': True
    })

@login_required
def view_diet_plan(request):
    """
    Display the generated diet plan.
    """
    plan_data = request.session.get('generated_diet_plan')
    
    if not plan_data:
        messages.warning(request, "No diet plan found. Please generate one first.")
        return redirect('ai_diet_plan')
    
    # Extract the actual plan dictionary
    if plan_data.get('success'):
        diet_plan = plan_data.get('plan')
    else:
        # If failed, use fallback plan if available
        diet_plan = plan_data.get('fallback_plan')
        if not diet_plan:
             diet_plan = {}
    
    return render(request, 'gym/view_diet_plan.html', {
        'plan': diet_plan
    })

@login_required
def member_insights(request):
    """
    View for members to see their own analytics and engagement score.
    """
    try:
        insights = AnalyticsService.get_member_insights(request.user.member_profile)
    except Exception as e:
        messages.error(request, f"Could not retrieve insights: {str(e)}")
        insights = {}
        
    return render(request, 'gym/member_insights.html', {
        'insights': insights
    })

@login_required
def gym_analytics(request):
    """
    Admin view for gym-wide analytics.
    """
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('dashboard')
        
    try:
        analytics = AnalyticsService.get_gym_analytics()
    except Exception as e:
        messages.error(request, f"Could not retrieve gym analytics: {str(e)}")
        analytics = {}
        
    return render(request, 'gym/gym_analytics.html', {
        'analytics': analytics
    })
