from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from core.models import CustomUser, MemberProfile, Attendance, Payment, Expense, ChatMessage, DietPlan, WorkoutVideo, LeaveRequest
from .forms import VideoForm, DietPlanForm, LeaveRequestForm, MemberAddForm, MemberEditForm
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from core.decorators import role_required

@login_required
def dashboard(request):
    user = request.user
    if user.is_superuser or user.role in ['admin', 'tenant_admin', 'super_admin']:
        return admin_dashboard(request)
    elif user.role == 'trainer':
        return trainer_dashboard(request)
    elif user.role == 'member':
        return member_dashboard(request)
    
    # Fallback
    return member_dashboard(request)

@login_required
def admin_dashboard(request):
    # Admin View Logic
    total_members = MemberProfile.objects.count()
    trainers_count = CustomUser.objects.filter(role='trainer').count()
    staff_count = CustomUser.objects.filter(role='staff').count()
    
    income = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    expense_total = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    profit = income - expense_total

    context = {
        'total_members': total_members,
        'trainers_count': trainers_count,
        'staff_count': staff_count,
        'income': income,
        'expense': expense_total,
        'profit': profit,
    }
    return render(request, 'gym/admin_dashboard.html', context)

@login_required
def trainer_dashboard(request):
    # Trainer View Logic
    total_members = MemberProfile.objects.count()
    # Logic for something specific to trainer could go here
    # For now, just total members and maybe recent payments?
    
    recent_payments = Payment.objects.order_by('-date')[:5]

    context = {
        'total_members': total_members,
        'recent_payments': recent_payments,
    }
    return render(request, 'gym/trainer_dashboard.html', context)

@login_required
@role_required(['member'])
def member_dashboard(request):
    member = request.user.member_profile
    today = timezone.now().date()
    
    # Payment Due Alert
    show_payment_alert = False
    days_until_due = (member.next_payment_date - today).days
    if 0 <= days_until_due <= 10:
        show_payment_alert = True
        
    # Attendance Stats (Mock logic for now, or simple count)
    total_attendance = Attendance.objects.filter(member=member, status='Present').count()
    
    context = {
        'member': member,
        'show_payment_alert': show_payment_alert,
        'days_until_due': days_until_due,
        'total_attendance': total_attendance,
    }
    return render(request, 'gym/member_dashboard.html', context)

@login_required
@role_required(['member'])
def member_attendance_history(request):
    member = request.user.member_profile
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    attendance_records = Attendance.objects.filter(member=member).order_by('-date', '-check_in_time')
    
    if date_from:
        attendance_records = attendance_records.filter(date__gte=date_from)
    if date_to:
        attendance_records = attendance_records.filter(date__lte=date_to)
        
    paginator = Paginator(attendance_records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'date_from': date_from,
        'date_to': date_to,
        'total_attended': Attendance.objects.filter(member=member, status='Present').count()
    }
    return render(request, 'gym/member_attendance.html', context)

@login_required
@role_required(['member'])
def member_payment_history(request):
    member = request.user.member_profile
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    payments = Payment.objects.filter(member=member).order_by('-date')
    
    if date_from:
        payments = payments.filter(date__gte=date_from)
    if date_to:
        payments = payments.filter(date__lte=date_to)
        
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'gym/member_payments.html', context)

@login_required
@role_required(['member'])
def member_video_list(request):
    search_query = request.GET.get('search', '')
    videos = WorkoutVideo.objects.all().order_by('-uploaded_at')
    
    if search_query:
        videos = videos.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        
    paginator = Paginator(videos, 6) # 6 videos per page for better layout
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'gym/member_videos.html', context)

@login_required
@role_required(['member'])
def member_diet_view(request):
    member = request.user.member_profile
    diet_plan = DietPlan.objects.filter(member=member).last()
    return render(request, 'gym/member_diet.html', {'diet_plan': diet_plan})

@login_required
@role_required(['member'])
def leave_request_create(request):
    member = request.user.member_profile
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.member = member
            leave.save()
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('member_dashboard')
    else:
        form = LeaveRequestForm()
    return render(request, 'gym/leave_request_form.html', {'form': form})

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin', 'trainer', 'staff'])
def member_list(request):
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    membership_filter = request.GET.get('membership', '')
    payment_status = request.GET.get('payment_status', '')
    
    # Base queryset
    members = MemberProfile.objects.all().select_related('user')
    
    # Apply filters
    if search_query:
        members = members.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    if membership_filter:
        members = members.filter(membership_type=membership_filter)
    
    if payment_status:
        today = timezone.now().date()
        if payment_status == 'due':
            members = members.filter(next_payment_date__lte=today)
        elif payment_status == 'upcoming':
            members = members.filter(next_payment_date__gt=today, next_payment_date__lte=today + timezone.timedelta(days=7))
    
    # Order by username
    members = members.order_by('user__username')
    
    # Pagination
    paginator = Paginator(members, 10)  # 10 members per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'membership_filter': membership_filter,
        'payment_status': payment_status,
        'membership_choices': MemberProfile.MEMBERSHIP_TYPES,
    }
    return render(request, 'gym/member_list.html', context)


@login_required
@role_required(['admin', 'tenant_admin', 'super_admin', 'trainer'])
def add_member(request):
        
    if request.method == 'POST':
        form = MemberAddForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if username or email exists
            if CustomUser.objects.filter(username=form.cleaned_data['username']).exists():
                form.add_error('username', 'Username already exists.')
            elif CustomUser.objects.filter(email=form.cleaned_data['email']).exists():
                form.add_error('email', 'Email already exists.')
            else:
                try:
                    # 1. Create User
                    user = CustomUser.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        role='member'
                    )
                
                    # 2. Create Profile
                    profile = form.save(commit=False)
                    profile.user = user
                    
                    # 3. Calculate Next Payment Date
                    if profile.membership_type == 'monthly':
                        profile.next_payment_date = profile.registration_date + timezone.timedelta(days=30)
                    elif profile.membership_type == 'yearly':
                        profile.next_payment_date = profile.registration_date + timezone.timedelta(days=365)
                    else:
                        profile.next_payment_date = profile.registration_date + timezone.timedelta(days=90)
                    
                    profile.save()
                    
                    # 4. Create Initial Payment Record
                    total_initial = profile.registration_amount + profile.monthly_amount
                    Payment.objects.create(
                        member=profile,
                        amount=total_initial,
                        payment_type='registration',
                        remarks='Initial Registration + Fee'
                    )
                    
                    messages.success(request, 'Member added successfully!')
                    return redirect('member_list')
                except Exception as e:
                    messages.error(request, f'Error creating member: {str(e)}')
    else:
        form = MemberAddForm()
    return render(request, 'gym/member_form.html', {'form': form, 'title': 'Add New Member'})

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin', 'trainer'])
def edit_member(request, member_id):
        
    member = get_object_or_404(MemberProfile, id=member_id)
    if request.method == 'POST':
        form = MemberEditForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member updated successfully!')
            return redirect('member_list')
    else:
        form = MemberEditForm(instance=member)
    return render(request, 'gym/member_form.html', {'form': form, 'title': 'Edit Member', 'is_edit': True})

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin'])
def delete_member(request, member_id):
    # Double check in case decorator list changes
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin']:
        messages.error(request, 'Only Admins can delete members.')
        return redirect('member_list')
        
    member = get_object_or_404(MemberProfile, id=member_id)
    user = member.user
    member.delete()
    user.delete()
    messages.success(request, 'Member deleted successfully!')
    return redirect('member_list')

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin', 'trainer', 'staff'])
def mark_attendance(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        status = request.POST.get('status', 'Present')
        member = get_object_or_404(MemberProfile, id=member_id)
        
        # Allow multiple check-ins per day (for different sessions)
        today = timezone.now().date()
        
        # Create attendance record
        Attendance.objects.create(
            tenant=request.tenant if hasattr(request, 'tenant') else None,
            member=member, 
            date=today, 
            check_in_time=timezone.now().time(),
            status=status
        )
        messages.success(request, f"Attendance marked for {member.user.username} at {timezone.now().strftime('%I:%M %p')}")
        
        return redirect('mark_attendance')
    
    # GET request - show attendance page
    today = timezone.now().date()
    members = MemberProfile.objects.all().select_related('user').order_by('user__username')
    
    # Get count of attendance records today per member
    from django.db.models import Count
    attendance_counts = Attendance.objects.filter(date=today).values('member_id').annotate(count=Count('id'))
    attendance_dict = {item['member_id']: item['count'] for item in attendance_counts}
    
    # Total attendance records today
    present_count = Attendance.objects.filter(date=today).count()
    
    context = {
        'members': members,
        'attendance_counts': attendance_dict,
        'today': today,
        'present_count': present_count,
        'total_count': members.count(),
    }
    return render(request, 'gym/mark_attendance.html', context)



@login_required
@role_required(['admin', 'tenant_admin', 'super_admin'])
def finance_overview(request):
        
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    expenses_all = Expense.objects.all().order_by('-date')
    
    if date_from:
        expenses_all = expenses_all.filter(date__gte=date_from)
    if date_to:
        expenses_all = expenses_all.filter(date__lte=date_to)
        
    income = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    expense_total = expenses_all.aggregate(Sum('amount'))['amount__sum'] or 0
    profit = income - expense_total
    
    paginator = Paginator(expenses_all, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'income': income,
        'expense_total': expense_total,
        'profit': profit,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'gym/finance.html', context)

@login_required
def chat_room(request, room_name='general'):
    messages_list = ChatMessage.objects.filter(room_name=room_name).select_related('sender').order_by('timestamp')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            ChatMessage.objects.create(
                sender=request.user,
                room_name=room_name,
                content=content
            )
            # If HTMX request, just return the messages list partial
            if request.headers.get('HX-Request'):
                 messages_list = ChatMessage.objects.filter(room_name=room_name).select_related('sender').order_by('timestamp')
                 return render(request, 'gym/partials/chat_message_list.html', {'messages': messages_list})
            return redirect('chat_room', room_name=room_name)
    
    # If HTMX polling request (GET)
    if request.headers.get('HX-Request'):
         return render(request, 'gym/partials/chat_message_list.html', {'messages': messages_list})
            
    return render(request, 'gym/chat.html', {'messages': messages_list, 'room_name': room_name})

@login_required
def member_qr(request):
    """Generate QR Code for Member"""
    import qrcode
    from django.http import HttpResponse
    
    # Content is the username (unique ID)
    data = request.user.username
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin', 'trainer', 'staff'])
def attendance_scan(request):
    """Handle QR Code Scan via HTMX"""
    from django.http import HttpResponse # Import here to be safe
    
    if request.method == 'POST':
        code = request.POST.get('code')
        if code:
            try:
                # Code is username
                member = MemberProfile.objects.get(user__username=code)
                
                # Mark attendance
                Attendance.objects.create(
                    tenant=getattr(request, 'tenant', None),
                    member=member,
                    date=timezone.now().date(),
                    check_in_time=timezone.now().time(),
                    status='Present'
                )
                
                msg = f'<div class="alert alert-success">Checked in: <strong>{member.user.username}</strong></div>'
                return HttpResponse(msg)
                
            except MemberProfile.DoesNotExist:
                return HttpResponse(f'<div class="alert alert-danger">Member not found: {code}</div>')
            except Exception as e:
                return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>')
                
    return HttpResponse('')

@login_required
def notification_check(request):
    """View to show due payments and send SMS reminders"""
    today = timezone.now().date()
    deadline = today + timezone.timedelta(days=10)
    
    tenant = getattr(request, 'tenant', None)
    due_members = MemberProfile.objects.filter(next_payment_date__range=[today, deadline]).select_related('user')
    if tenant:
        due_members = due_members.filter(tenant=tenant)
        
    if request.method == 'POST' and 'send_sms' in request.POST:
        if request.user.role not in ['admin', 'tenant_admin', 'super_admin']:
            messages.error(request, "Permission denied.")
            return redirect('notifications')
            
        from .sms_service import sms_service
        
        template = "Hello {name}, your gym membership is due on {due_date}. Please pay soon to avoid interruption."
        results = sms_service.send_bulk_sms(due_members, template)
        
        messages.success(request, f"SMS Reminders: {results['successful']} sent, {results['failed']} failed.")
        return redirect('notifications')
    
    return render(request, 'gym/notifications.html', {'due_members': due_members})


@login_required
@role_required(['admin', 'tenant_admin', 'super_admin'])
def reports_view(request):
    """Analytics and Reports for Admin"""
    
    tenant = getattr(request, 'tenant', None)
    
    # Revenue Stats (Last 6 Months)
    from django.db.models.functions import TruncMonth
    from datetime import datetime, timedelta
    
    six_months_ago = timezone.now() - timedelta(days=180)
    
    payments = Payment.objects.all()
    if tenant:
        payments = payments.filter(tenant=tenant)
    
    monthly_revenue = payments.filter(date__gte=six_months_ago)\
        .annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total=Sum('amount'))\
        .order_by('month')

    # Expense breakdown by category
    expenses = Expense.objects.all()
    if tenant:
        expenses = expenses.filter(tenant=tenant)
        
    expense_breakdown = expenses.values('category')\
        .annotate(total=Sum('amount'))\
        .order_by('-total')

    # Attendance Trends
    attendance = Attendance.objects.all()
    if tenant:
        attendance = attendance.filter(tenant=tenant)
        
    daily_attendance = attendance.filter(date__gte=timezone.now() - timedelta(days=30))\
        .values('date')\
        .annotate(count=Count('id'))\
        .order_by('date')

    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'monthly_revenue': monthly_revenue,
        'expense_breakdown': expense_breakdown,
        'daily_attendance': daily_attendance,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'profit': total_revenue - total_expenses,
    }
    
    return render(request, 'gym/reports.html', context)


@login_required
@role_required(['admin', 'tenant_admin', 'super_admin'])
def export_report_pdf(request):
    """Generate PDF report for the gym"""
        
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    from django.http import HttpResponse
    
    tenant = getattr(request, 'tenant', None)
    
    # Same logic as reports_view to get data
    from django.db.models.functions import TruncMonth
    from datetime import timedelta
    
    six_months_ago = timezone.now() - timedelta(days=180)
    
    payments = Payment.objects.all()
    expenses = Expense.objects.all()
    if tenant:
        payments = payments.filter(tenant=tenant)
        expenses = expenses.filter(tenant=tenant)
    
    monthly_revenue = payments.filter(date__gte=six_months_ago)\
        .annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total=Sum('amount'))\
        .order_by('month')

    expense_breakdown = expenses.values('category')\
        .annotate(total=Sum('amount'))\
        .order_by('-total')

    total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'monthly_revenue': monthly_revenue,
        'expense_breakdown': expense_breakdown,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'profit': total_revenue - total_expenses,
        'generate_date': timezone.now(),
        'tenant': tenant,
    }
    
    html = render_to_string('gym/report_pdf.html', context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="gym_report_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
@role_required(['trainer', 'admin', 'tenant_admin', 'super_admin'])
def trainer_attendance_view(request):
    
    search_query = request.GET.get('search', '')
    date_query = request.GET.get('date', '')
    
    attendance_records = Attendance.objects.select_related('member__user').order_by('-date', '-check_in_time')
    
    if search_query:
        attendance_records = attendance_records.filter(
            Q(member__user__username__icontains=search_query) |
            Q(member__user__email__icontains=search_query)
        )
    
    if date_query:
        attendance_records = attendance_records.filter(date=date_query)
        
    paginator = Paginator(attendance_records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'date_query': date_query,
    }
    return render(request, 'gym/attendance_list.html', context)

@login_required
@role_required(['trainer', 'admin', 'tenant_admin', 'super_admin'])
def upload_video(request):
        
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Video uploaded successfully!')
            return redirect('dashboard')
    else:
        form = VideoForm()
    return render(request, 'gym/video_upload.html', {'form': form})

@login_required
@role_required(['trainer', 'admin', 'tenant_admin', 'super_admin'])
def create_diet_plan(request):
        
    if request.method == 'POST':
        form = DietPlanForm(request.POST)
        if form.is_valid():
            diet_plan = form.save(commit=False)
            diet_plan.assigned_by = request.user
            diet_plan.save()
            messages.success(request, 'Diet plan assigned successfully!')
            return redirect('dashboard')
    else:
        form = DietPlanForm()
    return render(request, 'gym/diet_plan_form.html', {'form': form})

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin'])
def trainer_list(request):
    
    search_query = request.GET.get('search', '')
    trainers = CustomUser.objects.filter(role='trainer').order_by('username')
    
    if search_query:
        trainers = trainers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    paginator = Paginator(trainers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'gym/trainer_list.html', context)

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin', 'trainer'])
def leave_request_list(request):
        
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    leaves = LeaveRequest.objects.all().select_related('member__user', 'approved_by').order_by('-created_at')
    
    if status_filter:
        leaves = leaves.filter(status=status_filter)
    if date_filter:
        leaves = leaves.filter(start_date__lte=date_filter, end_date__gte=date_filter)

    paginator = Paginator(leaves, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'gym/leave_request_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter
    })

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin', 'trainer'])
def leave_request_action(request, leave_id):
        
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            leave.status = 'Approved'
            leave.approved_by = request.user
            leave.save()
            messages.success(request, 'Leave request approved.')
        elif action == 'reject':
            leave.status = 'Rejected'
            leave.approved_by = request.user
            leave.save()
            messages.success(request, 'Leave request rejected.')
            
    return redirect('leave_request_list')

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin', 'trainer'])
def send_whatsapp_message(request):
    """View for sending WhatsApp messages to members by time slot"""
    
    from .forms import WhatsAppMessageForm
    from .whatsapp_service import whatsapp_service
    from core.models import WhatsAppMessage
    
    # Check if WhatsApp is configured
    if not whatsapp_service.is_configured():
        messages.warning(request, 'WhatsApp service is not configured. Please contact administrator.')
    
    if request.method == 'POST':
        form = WhatsAppMessageForm(request.POST)
        if form.is_valid():
            time_slot = form.cleaned_data['time_slot']
            message_content = form.cleaned_data['message']
            
            # Get preview of recipients
            members = whatsapp_service.get_members_by_slot(time_slot)
            recipient_count = members.count()
            
            if recipient_count == 0:
                messages.warning(request, 'No members found in the selected time slot.')
                return render(request, 'gym/send_whatsapp.html', {'form': form})
            
            # Send messages
            try:
                whatsapp_log = whatsapp_service.send_to_time_slot(
                    time_slot=time_slot,
                    message_content=message_content,
                    sent_by_user=request.user
                )
                
                if whatsapp_log.status == 'sent':
                    messages.success(
                        request,
                        f'WhatsApp message sent successfully to {whatsapp_log.recipient_count} members!'
                    )
                elif whatsapp_log.status == 'failed':
                    messages.error(
                        request,
                        f'Failed to send WhatsApp messages. Error: {whatsapp_log.error_message}'
                    )
                else:
                    messages.warning(
                        request,
                        f'Message sent with some errors: {whatsapp_log.error_message}'
                    )
                
                return redirect('whatsapp_history')
                
            except Exception as e:
                messages.error(request, f'Error sending WhatsApp messages: {str(e)}')
    else:
        form = WhatsAppMessageForm()
    
    # Get preview of members for selected slot (for AJAX or initial load)
    context = {
        'form': form,
        'whatsapp_configured': whatsapp_service.is_configured(),
    }
    return render(request, 'gym/send_whatsapp.html', context)

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin', 'trainer'])
def whatsapp_history(request):
    """View message history"""
    
    from core.models import WhatsAppMessage
    
    status_filter = request.GET.get('status', '')
    slot_filter = request.GET.get('slot', '')
    
    messages_list = WhatsAppMessage.objects.all().select_related('sent_by').order_by('-sent_at')
    
    if status_filter:
        messages_list = messages_list.filter(status=status_filter)
    if slot_filter:
        messages_list = messages_list.filter(time_slot=slot_filter)
    
    # Pagination
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'slot_filter': slot_filter,
        'time_slots': MemberProfile.objects.values_list('allotted_slot', flat=True).distinct().order_by('allotted_slot')
    }
    return render(request, 'gym/whatsapp_history.html', context)

@login_required
@role_required(['admin', 'tenant_admin', 'super_admin'])
def bulk_import_phones(request):
    """Bulk import phone numbers from CSV"""
    
    from .forms import BulkPhoneImportForm
    import csv
    import io
    
    from django.core.exceptions import ValidationError # Added for validation
    
    if request.method == 'POST':
        form = BulkPhoneImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Read CSV file
            try:
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                success_count = 0
                error_count = 0
                errors = []
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        username = row.get('username', '').strip()
                        phone_number = row.get('phone_number', '').strip()
                        
                        if not username or not phone_number:
                            errors.append(f"Row {row_num}: Missing username or phone number")
                            error_count += 1
                            continue
                        
                        # Find member by username
                        try:
                            member = MemberProfile.objects.select_related('user').get(
                                user__username=username
                            )
                        except MemberProfile.DoesNotExist:
                            errors.append(f"Row {row_num}: Member '{username}' not found")
                            error_count += 1
                            continue
                        
                        # Validate phone number format
                        try:
                            phone_clean = MemberProfile.validate_phone(phone_number)
                            member.phone_number = phone_clean
                            member.save()
                            success_count += 1
                        except ValidationError as e:
                            errors.append(f"Row {row_num}: Invalid phone format for '{username}' - {str(e)}")
                            error_count += 1
                            continue
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: Error - {str(e)}")
                        error_count += 1
                
                # Show results
                if success_count > 0:
                    messages.success(
                        request,
                        f'Successfully imported {success_count} phone number(s)!'
                    )
                
                if error_count > 0:
                    error_msg = f'{error_count} error(s) occurred:<br>'
                    error_msg += '<br>'.join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        error_msg += f'<br>... and {len(errors) - 10} more errors'
                    messages.warning(request, error_msg)
                
                if success_count > 0:
                    return redirect('member_list')
                    
            except Exception as e:
                messages.error(request, f'Error reading CSV file: {str(e)}')
    else:
        form = BulkPhoneImportForm()
    
    context = {
        'form': form,
    }
    return render(request, 'gym/bulk_import_phones.html', context)


@login_required
@role_required(['admin', 'tenant_admin', 'super_admin'])
def branding_settings(request):
    """Manage tenant branding settings"""
    
    from .forms import BrandingForm
    from core.models import BrandingConfig
    
    tenant = request.user.tenant
    branding, created = BrandingConfig.objects.get_or_create(tenant=tenant)
    
    if request.method == 'POST':
        form = BrandingForm(request.POST, request.FILES, instance=branding)
        if form.is_valid():
            form.save()
            messages.success(request, 'Branding settings updated successfully!')
            return redirect('branding_settings')
    else:
        form = BrandingForm(instance=branding)
    
    return render(request, 'gym/branding_settings.html', {'form': form, 'branding': branding})
