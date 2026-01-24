"""
Booking Views
Handle class booking and calendar functionality
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

from core.booking_models import (
    ClassSchedule,
    ClassBooking,
    PersonalTrainingSession,
    BookingSettings
)
from core.models import MemberProfile
from core.decorators import role_required


@login_required
@role_required(['member'])
def class_calendar(request):
    """Display class calendar for members"""
    member = request.user.member_profile
    tenant = request.user.tenant
    
    # Get booking settings
    settings = BookingSettings.objects.filter(tenant=tenant).first()
    
    # Get all active class schedules
    schedules = ClassSchedule.objects.filter(
        tenant=tenant,
        is_active=True
    ).select_related('instructor')
    
    # Get member's bookings
    member_bookings = ClassBooking.objects.filter(
        member=member,
        status__in=['confirmed', 'waitlist']
    ).select_related('class_schedule')
    
    context = {
        'member': member,
        'schedules': schedules,
        'member_bookings': member_bookings,
        'settings': settings,
    }
    return render(request, 'gym/class_calendar.html', context)


@login_required
@role_required(['member'])
def get_calendar_events(request):
    """API endpoint for FullCalendar to fetch events"""
    tenant = request.user.tenant
    member = request.user.member_profile
    
    # Get date range from request
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    events = []
    
    # Get all class schedules
    schedules = ClassSchedule.objects.filter(
        tenant=tenant,
        is_active=True
    )
    
    # Convert schedules to calendar events
    if start and end:
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        
        for schedule in schedules:
            # Generate events for each occurrence within date range
            current_date = start_date.date()
            while current_date <= end_date.date():
                # Check if this day matches the schedule
                if current_date.weekday() == schedule.day_of_week:
                    # Check if member has booked this class
                    booking = ClassBooking.objects.filter(
                        member=member,
                        class_schedule=schedule,
                        booking_date=current_date
                    ).first()
                    
                    # Get current bookings count
                    bookings_count = ClassBooking.objects.filter(
                        class_schedule=schedule,
                        booking_date=current_date,
                        status='confirmed'
                    ).count()
                    
                    is_full = bookings_count >= schedule.capacity
                    
                    event = {
                        'id': f'{schedule.id}_{current_date}',
                        'title': f'{schedule.class_name} ({bookings_count}/{schedule.capacity})',
                        'start': f'{current_date}T{schedule.start_time}',
                        'end': f'{current_date}T{schedule.end_time}',
                        'backgroundColor': '#667eea' if not booking else ('#28a745' if booking.status == 'confirmed' else '#ffc107'),
                        'borderColor': '#667eea' if not booking else ('#28a745' if booking.status == 'confirmed' else '#ffc107'),
                        'extendedProps': {
                            'schedule_id': schedule.id,
                            'date': str(current_date),
                            'instructor': schedule.instructor.get_full_name() if schedule.instructor else 'TBA',
                            'capacity': schedule.capacity,
                            'booked': bookings_count,
                            'is_full': is_full,
                            'is_booked': booking is not None,
                            'booking_status': booking.status if booking else None,
                            'booking_id': booking.id if booking else None,
                        }
                    }
                    events.append(event)
                
                current_date += timedelta(days=1)
    
    return JsonResponse(events, safe=False)


@login_required
@role_required(['member'])
def book_class(request):
    """Book a class"""
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        booking_date = request.POST.get('booking_date')
        
        member = request.user.member_profile
        schedule = get_object_or_404(ClassSchedule, id=schedule_id, tenant=request.user.tenant)
        
        # Parse date
        try:
            booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})
        
        # Check if already booked
        existing_booking = ClassBooking.objects.filter(
            member=member,
            class_schedule=schedule,
            booking_date=booking_date,
            status__in=['confirmed', 'waitlist']
        ).first()
        
        if existing_booking:
            return JsonResponse({
                'success': False,
                'error': 'You have already booked this class'
            })
        
        # Check capacity
        confirmed_bookings = ClassBooking.objects.filter(
            class_schedule=schedule,
            booking_date=booking_date,
            status='confirmed'
        ).count()
        
        # Get booking settings
        settings = BookingSettings.objects.filter(tenant=request.user.tenant).first()
        allow_waitlist = settings.allow_waitlist if settings else True
        
        if confirmed_bookings >= schedule.capacity:
            if allow_waitlist:
                # Add to waitlist
                booking = ClassBooking.objects.create(
                    member=member,
                    class_schedule=schedule,
                    booking_date=booking_date,
                    status='waitlist'
                )
                return JsonResponse({
                    'success': True,
                    'message': 'Added to waitlist',
                    'status': 'waitlist'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Class is full and waitlist is not available'
                })
        
        # Create booking
        booking = ClassBooking.objects.create(
            member=member,
            class_schedule=schedule,
            booking_date=booking_date,
            status='confirmed'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Class booked successfully!',
            'booking_id': booking.id,
            'status': 'confirmed'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@role_required(['member'])
def cancel_booking(request, booking_id):
    """Cancel a class booking"""
    member = request.user.member_profile
    booking = get_object_or_404(ClassBooking, id=booking_id, member=member)
    
    # Check cancellation policy
    settings = BookingSettings.objects.filter(tenant=request.user.tenant).first()
    if settings and settings.cancellation_hours:
        hours_until_class = (datetime.combine(booking.booking_date, booking.class_schedule.start_time) - timezone.now()).total_seconds() / 3600
        if hours_until_class < settings.cancellation_hours:
            messages.error(request, f'Cannot cancel within {settings.cancellation_hours} hours of class')
            return redirect('my_bookings')
    
    # Cancel booking
    booking.status = 'cancelled'
    booking.cancelled_at = timezone.now()
    booking.save()
    
    # Promote from waitlist if applicable
    if settings and settings.allow_waitlist:
        waitlist_booking = ClassBooking.objects.filter(
            class_schedule=booking.class_schedule,
            booking_date=booking.booking_date,
            status='waitlist'
        ).order_by('booked_at').first()
        
        if waitlist_booking:
            waitlist_booking.status = 'confirmed'
            waitlist_booking.save()
            # TODO: Send notification to member
    
    messages.success(request, 'Booking cancelled successfully')
    return redirect('my_bookings')


@login_required
@role_required(['member'])
def my_bookings(request):
    """View member's bookings"""
    member = request.user.member_profile
    
    # Get upcoming bookings
    upcoming_bookings = ClassBooking.objects.filter(
        member=member,
        booking_date__gte=timezone.now().date(),
        status__in=['confirmed', 'waitlist']
    ).select_related('class_schedule', 'class_schedule__instructor').order_by('booking_date', 'class_schedule__start_time')
    
    # Get past bookings
    past_bookings = ClassBooking.objects.filter(
        member=member,
        booking_date__lt=timezone.now().date()
    ).select_related('class_schedule').order_by('-booking_date')[:10]
    
    context = {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
    }
    return render(request, 'gym/my_bookings.html', context)


@login_required
@role_required(['tenant_admin', 'trainer'])
def manage_class_schedules(request):
    """Admin view to manage class schedules"""
    tenant = request.user.tenant
    
    schedules = ClassSchedule.objects.filter(
        tenant=tenant
    ).select_related('instructor').order_by('day_of_week', 'start_time')
    
    context = {
        'schedules': schedules,
    }
    return render(request, 'gym/manage_class_schedules.html', context)
