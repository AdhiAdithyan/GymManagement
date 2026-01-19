# Gym Management System - New Features Documentation

## Recent Updates (January 2026)

This document describes the three new features added to the Gym Management System:

1. **Member Photo Identification**
2. **Multiple Daily Check-ins**
3. **WhatsApp Integration for Group Messaging**

---

## 1. Member Photo Identification

### Overview
Member profile photos are now displayed throughout the system for easy visual identification.

### Features
- **Member List**: Profile photos displayed next to member names
- **Attendance Marking**: Photos shown when marking attendance
- **Fallback Display**: If no photo is uploaded, member's initials are shown in a colored circle

### Usage
1. When adding or editing a member, upload a profile photo using the image field
2. Supported formats: JPG, PNG, GIF
3. Recommended size: 500x500 pixels or larger
4. Photos are automatically displayed in:
   - Member list (`/members/`)
   - Attendance marking interface (`/attendance/mark/`)
   - Other member-related views

---

## 2. Multiple Daily Check-ins

### Overview
Members can now check in multiple times per day, allowing for different training sessions (e.g., morning and evening workouts).

### Features
- **Unlimited Check-ins**: No restriction on number of daily check-ins
- **Timestamp Recording**: Each check-in records the exact time
- **Session Counter**: Shows how many times a member has checked in today
- **Grouped Display**: Attendance history groups check-ins by date

### Usage

#### For Admin/Trainer:
1. Navigate to **Mark Attendance** (`/attendance/mark/`)
2. Find the member in the list
3. Click **"Mark Present"** for first check-in
4. For additional check-ins, click **"Add Session"**
5. Each check-in will show with its timestamp

#### For Members:
1. View your attendance history at **My Attendance** (`/member/attendance/`)
2. Records are grouped by date
3. All check-in times for each day are displayed
4. Total sessions per day are shown

### Display Format
```
Date: January 19, 2026 (Saturday)
Check-in Times: 6:30 AM | 5:45 PM
Total Sessions: 2 sessions
Status: Present
```

---

## 3. WhatsApp Integration

### Overview
Send WhatsApp messages to groups of members based on their time slots. Perfect for announcements, schedule changes, or motivational messages.

### Prerequisites

#### Option A: Twilio WhatsApp API (Recommended for Production)
1. Create a Twilio account at https://www.twilio.com
2. Set up WhatsApp Business API
3. Get your credentials:
   - Account SID
   - Auth Token
   - WhatsApp-enabled phone number

#### Option B: Testing Without Twilio
The system will work without Twilio configured, but messages won't actually send. This is useful for testing the interface.

### Configuration

1. **Update `.env` file** with your Twilio credentials:
```env
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

2. **Install Twilio library** (if not already installed):
```bash
pip install twilio>=8.0.0
```

3. **Add Phone Numbers to Members**:
   - Currently, the system expects phone numbers to be added to member profiles
   - **Important**: You need to add a `phone_number` field to either the `CustomUser` or `MemberProfile` model
   - Phone numbers should be in international format: `+1234567890`

### Usage

#### Sending Messages

1. **Access WhatsApp Messaging**:
   - Admin Dashboard → Click "WhatsApp Messages" tile
   - Trainer Dashboard → Click "WhatsApp Messages" tile
   - Direct URL: `/whatsapp/send/`

2. **Compose Message**:
   - Select target group from dropdown:
     - "All Members" - sends to everyone
     - Specific time slot (e.g., "6:00 AM - 7:00 AM") - sends to members in that slot
   - Type your message in the text area
   - Character counter shows message length

3. **Send**:
   - Click "Send Message"
   - Confirmation dialog will appear
   - Messages are sent immediately
   - Success/failure notification will appear

#### Viewing Message History

1. Navigate to **WhatsApp History** (`/whatsapp/history/`)
2. View all sent messages with:
   - Date and time sent
   - Sender name and role
   - Target group
   - Number of recipients
   - Message preview
   - Delivery status (Sent/Failed/Pending)

### Message Templates

Here are some example messages you can use:

**Schedule Change:**
```
Hi! This is [Gym Name]. 
Tomorrow's 6 AM session is rescheduled to 7 AM due to maintenance. 
Sorry for the inconvenience!
```

**Motivational Message:**
```
Great work this week, team! 
Keep pushing towards your goals. 
See you at the gym! 💪
```

**Payment Reminder:**
```
Hello! This is a friendly reminder that your membership payment is due in 3 days. 
Please make the payment to avoid interruption. 
Thank you!
```

**Holiday Closure:**
```
[Gym Name] will be closed on [Date] for [Holiday]. 
We'll resume normal hours on [Date]. 
Have a great holiday!
```

### Best Practices

1. **Keep Messages Concise**: WhatsApp is best for short, clear messages
2. **Include Gym Name**: Always identify yourself in the message
3. **Timing**: Send messages during reasonable hours
4. **Frequency**: Don't spam - limit to important announcements
5. **Test First**: Send to a small group before broadcasting to all
6. **Phone Number Format**: Ensure all member phone numbers are in international format (+country code)

### Troubleshooting

#### "WhatsApp service not configured"
- Check that your `.env` file has the correct Twilio credentials
- Restart the Django server after updating `.env`

#### "No phone numbers found for members in this slot"
- Add phone numbers to member profiles
- Ensure phone numbers are in international format: `+1234567890`

#### Messages show as "Failed"
- Check Twilio account balance
- Verify WhatsApp number is properly configured in Twilio
- Check error message in the history view
- Ensure recipient phone numbers are valid

#### Messages not being received
- Verify recipients have WhatsApp installed
- Check that recipients have opted in to receive WhatsApp messages (Twilio requirement)
- Review Twilio logs for delivery status

---

## Database Changes

### New Model: WhatsAppMessage

Tracks all sent WhatsApp messages:

```python
class WhatsAppMessage(models.Model):
    tenant = ForeignKey(Tenant)
    sent_by = ForeignKey(CustomUser)
    recipients = JSONField  # List of member IDs
    time_slot = CharField  # Target slot or 'all'
    message_content = TextField
    sent_at = DateTimeField
    status = CharField  # 'pending', 'sent', 'failed'
    error_message = TextField
    recipient_count = IntegerField
```

### Migration

The migration file `0007_whatsappmessage.py` has been created and applied.

---

## API Endpoints

### WhatsApp Routes
- `GET/POST /whatsapp/send/` - Send WhatsApp message form
- `GET /whatsapp/history/` - View message history

### Permissions
- Only Admin, Tenant Admin, and Trainer roles can access WhatsApp features
- Members cannot send WhatsApp messages

---

## Files Modified/Created

### New Files
- `gym/whatsapp_service.py` - WhatsApp service module
- `templates/gym/send_whatsapp.html` - Send message interface
- `templates/gym/whatsapp_history.html` - Message history view
- `core/migrations/0007_whatsappmessage.py` - Database migration

### Modified Files
- `requirements.txt` - Added `twilio>=8.0.0`
- `.env.example` - Added Twilio configuration
- `core/models.py` - Added WhatsAppMessage model
- `gym/forms.py` - Added WhatsAppMessageForm
- `gym/views.py` - Added WhatsApp views
- `gym/urls.py` - Added WhatsApp routes
- `gym_management/settings.py` - Added Twilio configuration
- `templates/gym/admin_dashboard.html` - Added WhatsApp tile
- `templates/gym/trainer_dashboard.html` - Added WhatsApp tile
- `templates/gym/member_attendance.html` - Enhanced to show multiple check-ins
- `templates/gym/mark_attendance.html` - Already had photo support

---

## Future Enhancements

### Planned Features
1. **Phone Number Field**: Add dedicated phone_number field to MemberProfile
2. **SMS Integration**: Add SMS as alternative to WhatsApp
3. **Message Templates**: Pre-defined message templates
4. **Scheduled Messages**: Schedule messages for future delivery
5. **Message Analytics**: Track open rates and engagement
6. **Two-way Messaging**: Receive and respond to member messages
7. **Bulk Import**: Import phone numbers from CSV
8. **Message History Export**: Export message logs to CSV/PDF

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Twilio documentation: https://www.twilio.com/docs/whatsapp
3. Contact your system administrator

---

## Version History

- **v3.1.0** (January 2026)
  - Added WhatsApp integration
  - Enhanced multiple daily check-ins display
  - Improved member photo identification

- **v3.0.0** (December 2025)
  - Initial multi-tenant support
  - REST API implementation
  - Leave management system

---

**Last Updated**: January 19, 2026
