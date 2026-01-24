"""
WhatsApp Service Module
Handles sending WhatsApp messages to gym members using Twilio API
Supports Multi-tenancy with per-gym Twilio credentials
"""

from twilio.rest import Client
from django.conf import settings
from core.models import MemberProfile, WhatsAppMessage, BrandingConfig
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service class for WhatsApp messaging operations"""
    
    def __init__(self):
        """Initialize Twilio client with defaults from settings"""
        # Default global credentials from settings
        self.default_account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.default_auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.default_whatsapp_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', None)
        
        # We don't initialize a static client here anymore, 
        # as it can vary per request/tenant.
    
    def get_client(self, tenant=None):
        """
        Get an initialized Twilio Client and sender number.
        Tries tenant-specific credentials first, then falls back to settings.
        """
        account_sid = self.default_account_sid
        auth_token = self.default_auth_token
        whatsapp_number = self.default_whatsapp_number
        
        # Check for tenant-specific credentials
        if tenant:
            try:
                branding = BrandingConfig.objects.filter(tenant=tenant).first()
                if branding and branding.twilio_account_sid and branding.twilio_auth_token:
                    account_sid = branding.twilio_account_sid
                    auth_token = branding.twilio_auth_token
                    whatsapp_number = branding.twilio_whatsapp_number or whatsapp_number
                    logger.info(f"Using tenant-specific Twilio credentials for: {tenant.name}")
            except Exception as e:
                logger.error(f"Error fetching tenant credentials: {str(e)}")

        if account_sid and auth_token:
            try:
                return Client(account_sid, auth_token), whatsapp_number
            except Exception as e:
                logger.error(f"Failed to initialize Twilio Client: {str(e)}")
        
        return None, whatsapp_number
    
    def is_configured(self, tenant=None):
        """Check if WhatsApp service is properly configured (tenant or global)"""
        client, num = self.get_client(tenant)
        return client is not None
    
    def format_phone_number(self, phone):
        """
        Format phone number for WhatsApp
        Expects phone in format: +1234567890 or 1234567890
        Returns: whatsapp:+1234567890
        """
        if not phone:
            return None
        
        # Remove any spaces, dashes, or parentheses
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Add + if not present
        if not phone.startswith('+'):
            phone = '+' + phone
        
        # Add whatsapp: prefix
        if not phone.startswith('whatsapp:'):
            phone = 'whatsapp:' + phone
        
        return phone
    
    def send_message(self, phone_number, message_content, tenant=None):
        """
        Send WhatsApp message to a single recipient
        """
        client, whatsapp_number = self.get_client(tenant)
        
        if not client:
            return {
                'success': False,
                'message_sid': None,
                'error': 'WhatsApp service not configured for this gym'
            }
        
        try:
            formatted_number = self.format_phone_number(phone_number)
            if not formatted_number:
                return {
                    'success': False,
                    'message_sid': None,
                    'error': 'Invalid phone number'
                }
            
            message = client.messages.create(
                body=message_content,
                from_=whatsapp_number,
                to=formatted_number
            )
            
            logger.info(f"WhatsApp message sent successfully. SID: {message.sid}")
            return {
                'success': True,
                'message_sid': message.sid,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return {
                'success': False,
                'message_sid': None,
                'error': str(e)
            }
    
    def send_bulk_messages(self, phone_numbers, message_content, tenant=None):
        """Send WhatsApp message to multiple recipients"""
        results = {
            'total': len(phone_numbers),
            'successful': 0,
            'failed': 0,
            'results': []
        }
        
        for phone in phone_numbers:
            result = self.send_message(phone, message_content, tenant=tenant)
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
            results['results'].append({
                'phone': phone,
                'success': result['success'],
                'error': result.get('error')
            })
        
        return results
    
    def get_members_by_slot(self, time_slot, tenant=None):
        """
        Get all members in a specific time slot for a specific tenant
        """
        if time_slot == 'all':
            return MemberProfile.objects.filter(tenant=tenant).select_related('user')
        else:
            return MemberProfile.objects.filter(
                tenant=tenant,
                allotted_slot=time_slot
            ).select_related('user')

    def send_to_time_slot(self, time_slot, message_content, sent_by_user):
        """Send WhatsApp message to all members in a specific time slot"""
        tenant = getattr(sent_by_user, 'tenant', None)
        
        # Get members in the time slot + tenant isolation
        if time_slot == 'all':
            members = MemberProfile.objects.filter(tenant=tenant).select_related('user')
        else:
            members = MemberProfile.objects.filter(tenant=tenant, allotted_slot=time_slot).select_related('user')
        
        whatsapp_log = WhatsAppMessage.objects.create(
            tenant=tenant,
            sent_by=sent_by_user,
            time_slot=time_slot,
            message_content=message_content,
            status='pending',
            recipient_count=members.count()
        )
        
        phone_numbers = []
        member_ids = []
        
        for member in members:
            if member.phone_number:
                phone_numbers.append(member.phone_number)
                member_ids.append(member.id)
        
        if phone_numbers:
            results = self.send_bulk_messages(phone_numbers, message_content, tenant=tenant)
            
            whatsapp_log.recipients = member_ids
            whatsapp_log.recipient_count = len(member_ids)
            
            if results['failed'] == 0:
                whatsapp_log.status = 'sent'
            elif results['successful'] > 0:
                whatsapp_log.status = 'sent'
                whatsapp_log.error_message = f"{results['failed']} messages failed to send"
            else:
                whatsapp_log.status = 'failed'
                whatsapp_log.error_message = "All messages failed to send"
            
            whatsapp_log.save()
        else:
            whatsapp_log.status = 'failed'
            whatsapp_log.error_message = 'No phone numbers found for members in this slot'
            whatsapp_log.save()
        
        return whatsapp_log


# Singleton instance
whatsapp_service = WhatsAppService()
