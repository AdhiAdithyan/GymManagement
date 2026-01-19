"""
WhatsApp Service Module
Handles sending WhatsApp messages to gym members using Twilio API
"""

from twilio.rest import Client
from django.conf import settings
from core.models import MemberProfile, WhatsAppMessage
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service class for WhatsApp messaging operations"""
    
    def __init__(self):
        """Initialize Twilio client with credentials from settings"""
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.whatsapp_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', None)
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.warning("Twilio credentials not configured. WhatsApp service disabled.")
    
    def is_configured(self):
        """Check if WhatsApp service is properly configured"""
        return self.client is not None
    
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
    
    def send_message(self, phone_number, message_content):
        """
        Send WhatsApp message to a single recipient
        
        Args:
            phone_number: Phone number in format +1234567890
            message_content: Message text to send
            
        Returns:
            dict: {'success': bool, 'message_sid': str or None, 'error': str or None}
        """
        if not self.is_configured():
            return {
                'success': False,
                'message_sid': None,
                'error': 'WhatsApp service not configured'
            }
        
        try:
            formatted_number = self.format_phone_number(phone_number)
            if not formatted_number:
                return {
                    'success': False,
                    'message_sid': None,
                    'error': 'Invalid phone number'
                }
            
            message = self.client.messages.create(
                body=message_content,
                from_=self.whatsapp_number,
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
    
    def send_bulk_messages(self, phone_numbers, message_content):
        """
        Send WhatsApp message to multiple recipients
        
        Args:
            phone_numbers: List of phone numbers
            message_content: Message text to send
            
        Returns:
            dict: {
                'total': int,
                'successful': int,
                'failed': int,
                'results': list of dicts
            }
        """
        results = {
            'total': len(phone_numbers),
            'successful': 0,
            'failed': 0,
            'results': []
        }
        
        for phone in phone_numbers:
            result = self.send_message(phone, message_content)
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
    
    def get_members_by_slot(self, time_slot):
        """
        Get all members in a specific time slot
        
        Args:
            time_slot: Time slot string (e.g., "6:00 AM - 7:00 AM") or "all"
            
        Returns:
            QuerySet of MemberProfile objects
        """
        if time_slot == 'all':
            return MemberProfile.objects.all().select_related('user')
        else:
            return MemberProfile.objects.filter(
                allotted_slot=time_slot
            ).select_related('user')
    
    def send_to_time_slot(self, time_slot, message_content, sent_by_user):
        """
        Send WhatsApp message to all members in a specific time slot
        
        Args:
            time_slot: Time slot string or "all"
            message_content: Message text to send
            sent_by_user: CustomUser who is sending the message
            
        Returns:
            WhatsAppMessage object with results
        """
        # Get members in the time slot
        members = self.get_members_by_slot(time_slot)
        
        # Create WhatsApp message log
        whatsapp_log = WhatsAppMessage.objects.create(
            sent_by=sent_by_user,
            time_slot=time_slot,
            message_content=message_content,
            status='pending',
            recipient_count=members.count()
        )
        
        # Collect phone numbers (assuming phone is stored in user model or member profile)
        # Note: You may need to add a phone_number field to MemberProfile or CustomUser
        phone_numbers = []
        member_ids = []
        
        for member in members:
            # Try to get phone from user's email or add a phone field
            # For now, we'll use a placeholder - you need to add phone_number field
            if hasattr(member.user, 'phone_number') and member.user.phone_number:
                phone_numbers.append(member.user.phone_number)
                member_ids.append(member.id)
            elif hasattr(member, 'phone_number') and member.phone_number:
                phone_numbers.append(member.phone_number)
                member_ids.append(member.id)
        
        # Send messages
        if phone_numbers:
            results = self.send_bulk_messages(phone_numbers, message_content)
            
            # Update log
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
    
    def get_unique_time_slots(self):
        """Get list of unique time slots from all members"""
        slots = MemberProfile.objects.values_list(
            'allotted_slot', flat=True
        ).distinct().order_by('allotted_slot')
        return list(slots)


# Singleton instance
whatsapp_service = WhatsAppService()
