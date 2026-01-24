from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import MemberProfile, BrandingConfig, WhatsAppMessage
from gym.whatsapp_service import whatsapp_service
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically send WhatsApp payment reminders based on tenant settings'

    def handle(self, *args, **options):
        self.stdout.write("Checking for pending payment reminders...")
        
        # 1. Get all tenants with auto-reminders enabled
        branding_configs = BrandingConfig.objects.filter(enable_auto_whatsapp_reminders=True)
        
        if not branding_configs.exists():
            self.stdout.write(self.style.WARNING("No tenants have automatic WhatsApp reminders enabled."))
            return

        total_sent = 0
        total_failed = 0
        today = timezone.now().date()
        
        for config in branding_configs:
            tenant = config.tenant
            days_before = config.whatsapp_reminder_days_before
            self.stdout.write(f"Processing reminders for tenant: {tenant.name} (Window: {days_before} days)")
            
            # Target date 1: The specific reminder day (e.g. 7 days before)
            reminder_date = today + timedelta(days=days_before)
            
            # Find members whose payment is exactly on the reminder date
            # OR whose payment is due today
            # OR whose payment is overdue
            
            # Filter 1: Members due in exactly X days
            to_remind = MemberProfile.objects.filter(
                tenant=tenant,
                next_payment_date=reminder_date,
                phone_number__isnull=False
            ).exclude(phone_number='')

            # Filter 2: Members due today (as a final nudge)
            due_today = MemberProfile.objects.filter(
                tenant=tenant,
                next_payment_date=today,
                phone_number__isnull=False
            ).exclude(phone_number='')

            # Filter 3: Members overdue (within a 7 day window after due date)
            overdue = MemberProfile.objects.filter(
                tenant=tenant,
                next_payment_date__lt=today,
                next_payment_date__gte=today - timedelta(days=7),
                phone_number__isnull=False
            ).exclude(phone_number='')
            
            # Combine all (use union or just list them)
            # We'll process them in batches
            
            all_members = list(to_remind) + list(due_today) + list(overdue)
            
            for member in all_members:
                # Check if we already sent a reminder today
                already_sent = WhatsAppMessage.objects.filter(
                    tenant=tenant,
                    recipients__contains=[member.id],
                    time_slot='auto_payment_reminder',
                    sent_at__date=today
                ).exists()
                
                if already_sent:
                    continue
                
                # Construct message logic
                gym_name = tenant.name
                amount = member.monthly_amount
                due_date_str = member.next_payment_date.strftime('%B %d, %Y')
                first_name = member.user.first_name or member.user.username
                
                if member.next_payment_date == reminder_date:
                    message_content = f"Hello {first_name}, this is an automatic reminder from {gym_name}. Your gym subscription payment of {amount} is due in {days_before} days ({due_date_str}). Looking forward to seeing you at the gym!"
                elif member.next_payment_date == today:
                    message_content = f"Hello {first_name}, this is an automatic reminder from {gym_name}. Just a final nudge that your gym payment of {amount} is due today. Have a great workout!"
                else:
                    days_overdue = (today - member.next_payment_date).days
                    message_content = f"Hello {first_name}, this is an automatic reminder from {gym_name}. Your gym payment of {amount} is {days_overdue} days overdue. Please clear it today to continue your membership. Thank you!"
                
                # Send message
                if whatsapp_service.is_configured(tenant=tenant):
                    result = whatsapp_service.send_message(member.phone_number, message_content, tenant=tenant)
                    
                    WhatsAppMessage.objects.create(
                        tenant=tenant,
                        sent_by=None,
                        recipients=[member.id],
                        message_content=message_content,
                        status='sent' if result['success'] else 'failed',
                        error_message=result.get('error', '') if not result['success'] else '',
                        recipient_count=1,
                        time_slot='auto_payment_reminder'
                    )
                    
                    if result['success']:
                        total_sent += 1
                        self.stdout.write(self.style.SUCCESS(f"Sent to {member.user.username} (Due: {due_date_str})"))
                    else:
                        total_failed += 1
                
        self.stdout.write(self.style.SUCCESS(f"Finished! Total sent: {total_sent}, Total failed: {total_failed}"))
