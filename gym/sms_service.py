"""
SMS Service Module
Handles sending SMS messages to gym members using Twilio API
"""

from twilio.rest import Client
from django.conf import settings
from core.models import MemberProfile
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """Service class for SMS messaging operations"""
    
    def __init__(self):
        """Initialize Twilio client with credentials from settings"""
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.twilio_number = getattr(settings, 'TWILIO_SMS_NUMBER', None) # Note: Need to add this to settings
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.warning("Twilio credentials not configured. SMS service disabled.")
    
    def is_configured(self):
        """Check if SMS service is properly configured"""
        return self.client is not None
    
    def send_sms(self, phone_number, message_content):
        """
        Send SMS message to a single recipient
        
        Args:
            phone_number: Phone number in international format (+1234567890)
            message_content: Message text to send (max 160 chars recommended)
            
        Returns:
            dict: {'success': bool, 'message_sid': str or None, 'error': str or None}
        """
        if not self.is_configured():
            return {
                'success': False,
                'message_sid': None,
                'error': 'SMS service not configured'
            }
        
        try:
            # Basic validation
            if not phone_number or not phone_number.startswith('+'):
                return {
                    'success': False,
                    'message_sid': None,
                    'error': 'Invalid phone number format. Must start with +'
                }
            
            message = self.client.messages.create(
                body=message_content,
                from_=self.twilio_number or getattr(settings, 'TWILIO_WHATSAPP_NUMBER', '').replace('whatsapp:', ''),
                to=phone_number
            )
            
            logger.info(f"SMS sent successfully. SID: {message.sid}")
            return {
                'success': True,
                'message_sid': message.sid,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return {
                'success': False,
                'message_sid': None,
                'error': str(e)
            }
    
    def send_bulk_sms(self, members_queryset, message_template):
        """
        Send SMS to multiple members
        
        Args:
            members_queryset: QuerySet of MemberProfile objects
            message_template: String with placeholders like {name}
            
        Returns:
            dict: Summary of results
        """
        results = {
            'total': members_queryset.count(),
            'successful': 0,
            'failed': 0
        }
        
        for member in members_queryset:
            phone = member.phone_number
            if not phone:
                results['failed'] += 1
                continue
                
            # Customize message
            message = message_template.format(
                name=member.user.username,
                due_date=str(member.next_payment_date)
            )
            
            res = self.send_sms(phone, message)
            if res['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
                
        return results

# Singleton instance
sms_service = SMSService()
