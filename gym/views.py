from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from core.models import CustomUser, MemberProfile, Attendance, Payment, Expense, ChatMessage, DietPlan, WorkoutVideo, LeaveRequest
from .forms import VideoForm, DietPlanForm, LeaveRequestForm, MemberAddForm, MemberEditForm
from django.db.models import Sum, Q
from django.core.paginator import Paginator

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
def member_attendance_history(request):
    member = request.user.member_profile
    attendance_records = Attendance.objects.filter(member=member).order_by('-date')
    return render(request, 'gym/member_attendance.html', {'attendance_records': attendance_records})

@login_required
def member_payment_history(request):
    member = request.user.member_profile
    payments = Payment.objects.filter(member=member).order_by('-date')
    return render(request, 'gym/member_payments.html', {'payments': payments})

@login_required
def member_video_list(request):
    videos = WorkoutVideo.objects.all().order_by('-uploaded_at')
    return render(request, 'gym/member_videos.html', {'videos': videos})

@login_required
def member_diet_view(request):
    member = request.user.member_profile
    diet_plan = DietPlan.objects.filter(member=member).last()
    return render(request, 'gym/member_diet.html', {'diet_plan': diet_plan})

@login_required
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
@login_required
def member_list(request):
    # Restrict to Admin, Trainer, Staff
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin', 'trainer', 'staff']:
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    membership_filter = request.GET.get('membership', '')
    payment_status = request.GET.get('payment_status', '')
    
    # Base queryset
    members = MemberProfile.objects.all().select_related('user')
    
    # Apply filters
    if search_query:
        members = members.filter(
            models.Q(user__username__icontains=search_query) |
            models.Q(user__email__icontains=search_query) |
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query)
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
    from django.core.paginator import Paginator
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
def add_member(request):
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin', 'trainer']:
        return redirect('dashboard')
        
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
                except Exception as e:
                    messages.error(request, f'Error creating member: {str(e)}')
    else:
        form = MemberAddForm()
    return render(request, 'gym/member_form.html', {'form': form, 'title': 'Add New Member'})

@login_required
def edit_member(request, member_id):
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin', 'trainer']:
        return redirect('dashboard')
        
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
def delete_member(request, member_id):
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
def finance_overview(request):
    expenses = Expense.objects.all().order_by('-date')
    income = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    expense_total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    profit = income - expense_total
    
    context = {
        'expenses': expenses,
        'income': income,
        'expense_total': expense_total,
        'profit': profit
    }
    return render(request, 'gym/finance.html', context)

@login_required
def chat_room(request, room_name='general'):
    messages_list = ChatMessage.objects.filter(room_name=room_name).order_by('timestamp')
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            ChatMessage.objects.create(
                sender=request.user,
                room_name=room_name,
                content=content
            )
            return redirect('chat_room', room_name=room_name)
            
    return render(request, 'gym/chat.html', {'messages': messages_list, 'room_name': room_name})

@login_required
def notification_check(request):
    # Simple view to show due payments
    # Logic: next_payment_date <= today + 10 days
    today = timezone.now().date()
    deadline = today + timezone.timedelta(days=10)
    due_members = MemberProfile.objects.filter(next_payment_date__range=[today, deadline])
    
    return render(request, 'gym/notifications.html', {'due_members': due_members})

@login_required
def trainer_attendance_view(request):
    if request.user.role not in ['trainer', 'admin', 'tenant_admin', 'super_admin']:
        return redirect('dashboard')
    
    attendance_records = Attendance.objects.select_related('member__user').order_by('-date', '-check_in_time')
    return render(request, 'gym/attendance_list.html', {'attendance_records': attendance_records})

@login_required
def upload_video(request):
    if request.user.role not in ['trainer', 'admin', 'tenant_admin', 'super_admin']:
        return redirect('dashboard')
        
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
def create_diet_plan(request):
    if request.user.role not in ['trainer', 'admin', 'tenant_admin', 'super_admin']:
        return redirect('dashboard')
        
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
def trainer_list(request):
    # Only admin should see this or maybe all? Let's allow admin for now.
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin']:
        return redirect('dashboard')
    
    trainers = CustomUser.objects.filter(role='trainer')
    return render(request, 'gym/trainer_list.html', {'trainers': trainers})

@login_required
def leave_request_list(request):
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin', 'trainer']:
        return redirect('dashboard')
        
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
def leave_request_action(request, leave_id):
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin', 'trainer']:
        return redirect('dashboard')
        
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
def send_whatsapp_message(request):
    """View for sending WhatsApp messages to members by time slot"""
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin', 'trainer']:
        messages.error(request, 'You do not have permission to send WhatsApp messages.')
        return redirect('dashboard')
    
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
def whatsapp_history(request):
    """View message history"""
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin', 'trainer']:
        return redirect('dashboard')
    
    from core.models import WhatsAppMessage
    
    messages_list = WhatsAppMessage.objects.all().select_related('sent_by').order_by('-sent_at')
    
    # Pagination
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'gym/whatsapp_history.html', context)

@login_required
def bulk_import_phones(request):
    """Bulk import phone numbers from CSV"""
    if request.user.role not in ['admin', 'tenant_admin', 'super_admin']:
        messages.error(request, 'Only administrators can import phone numbers.')
        return redirect('dashboard')
    
    from .forms import BulkPhoneImportForm
    import csv
    import io
    import re
    
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
                        phone_clean = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                        if not re.match(r'^\+\d{10,15}$', phone_clean):
                            errors.append(f"Row {row_num}: Invalid phone format for '{username}'. Use +1234567890")
                            error_count += 1
                            continue
                        
                        # Update phone number
                        member.phone_number = phone_clean
                        member.save()
                        success_count += 1
                        
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

