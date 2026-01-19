from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('members/', views.member_list, name='member_list'),
    path('members/add/', views.add_member, name='add_member'),
    path('members/edit/<int:member_id>/', views.edit_member, name='edit_member'),
    path('members/delete/<int:member_id>/', views.delete_member, name='delete_member'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('finance/', views.finance_overview, name='finance'),
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
]
