from django.urls import path
from . import views
from . import payment_views  # Import payment views
from . import booking_views  # Import booking views
from . import ai_views       # Import AI views
from . import gamification_views # Import Gamification views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('members/', views.member_list, name='member_list'),
    path('members/add/', views.add_member, name='add_member'),
    path('members/edit/<int:member_id>/', views.edit_member, name='edit_member'),
    path('members/delete/<int:member_id>/', views.delete_member, name='delete_member'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/scan/', views.attendance_scan, name='attendance_scan'), # New
    path('member/qr/', views.member_qr, name='member_qr'), # New
    path('finance/', views.finance_overview, name='finance'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/export/', views.export_report_pdf, name='export_report_pdf'),
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),
    path('notifications/', views.notification_check, name='notifications'),
    path('trainer/attendance/', views.trainer_attendance_view, name='trainer_attendance'),
    path('trainer/video/upload/', views.upload_video, name='upload_video'),
    path('trainer/diet/create/', views.create_diet_plan, name='create_diet_plan'),
    path('manage/trainers/', views.trainer_list, name='trainer_list'),
    
    path('leave/list/', views.leave_request_list, name='leave_request_list'),
    path('leave/action/<int:leave_id>/', views.leave_request_action, name='leave_request_action'),

    # WhatsApp Routes
    path('whatsapp/send/', views.send_whatsapp_message, name='send_whatsapp'),
    path('whatsapp/history/', views.whatsapp_history, name='whatsapp_history'),
    path('members/import-phones/', views.bulk_import_phones, name='bulk_import_phones'),
    path('branding/', views.branding_settings, name='branding_settings'),

    # Member Routes
    path('member/dashboard/', views.member_dashboard, name='member_dashboard'),
    path('member/attendance/', views.member_attendance_history, name='member_attendance'),
    path('member/payments/', views.member_payment_history, name='member_payments'),
    path('member/videos/', views.member_video_list, name='member_videos'),
    path('member/diet/', views.member_diet_view, name='member_diet'),
    path('member/leave/', views.leave_request_create, name='leave_request'),
    
    # ============================================
    # PHASE 1 MODERNIZATION - PAYMENT ROUTES
    # ============================================
    
    # Member Payment Routes
    path('payments/', payment_views.payment_dashboard, name='payment_dashboard'),
    path('payments/create/', payment_views.create_payment, name='create_payment'),
    path('payments/success/<int:payment_id>/', payment_views.payment_success, name='payment_success'),
    path('payments/history/', payment_views.payment_history, name='payment_history'),
    
    # Admin Payment Routes
    path('admin/payments/', payment_views.admin_payment_overview, name='admin_payment_overview'),
    path('admin/payment-settings/', payment_views.payment_gateway_settings, name='payment_gateway_settings'),
    
    # Webhook Routes (no authentication required)
    path('webhooks/stripe/', payment_views.stripe_webhook, name='stripe_webhook'),
    
    # ============================================
    # PHASE 1 MODERNIZATION - BOOKING ROUTES
    # ============================================
    
    # Member Booking Routes
    path('classes/', booking_views.class_calendar, name='class_calendar'),
    path('classes/events/', booking_views.get_calendar_events, name='get_calendar_events'),
    path('classes/book/', booking_views.book_class, name='book_class'),
    path('bookings/', booking_views.my_bookings, name='my_bookings'),
    path('bookings/cancel/<int:booking_id>/', booking_views.cancel_booking, name='cancel_booking'),
    
    # Admin/Trainer Booking Routes
    path('admin/schedules/', booking_views.manage_class_schedules, name='manage_class_schedules'),

    # ============================================
    # PHASE 2 MODERNIZATION - AI ROUTES
    # ============================================
    path('ai/workout/generate/', ai_views.ai_workout_plan, name='ai_workout_plan'),
    path('ai/workout/view/', ai_views.view_workout_plan, name='view_workout_plan'),
    path('ai/diet/generate/', ai_views.ai_diet_plan, name='ai_diet_plan'),
    path('ai/diet/view/', ai_views.view_diet_plan, name='view_diet_plan'),
    path('ai/analytics/member/', ai_views.member_insights, name='member_insights'),
    path('ai/analytics/gym/', ai_views.gym_analytics, name='gym_analytics'),
    
    # ============================================
    # PHASE 2 MODERNIZATION - GAMIFICATION ROUTES
    # ============================================
    path('gamification/log/', gamification_views.log_workout, name='log_workout'),
    path('gamification/leaderboard/', gamification_views.leaderboard, name='leaderboard'),
    path('gamification/achievements/', gamification_views.achievements_view, name='achievements'),
] # Phase 2 Routes Loaded
