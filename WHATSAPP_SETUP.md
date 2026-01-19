# WhatsApp Integration Setup Guide

## Quick Start Guide

Follow these steps to set up WhatsApp messaging in your Gym Management System.

## Step 1: Choose Your Integration Method

### Option A: Twilio WhatsApp API (Recommended)
**Best for**: Production use, reliable delivery, professional setup
**Cost**: Pay-per-message (check Twilio pricing)
**Setup Time**: 30-60 minutes

### Option B: Test Mode (No Real Messages)
**Best for**: Testing the interface without sending real messages
**Cost**: Free
**Setup Time**: 5 minutes

---

## Step 2: Twilio Setup (Option A Only)

### 2.1 Create Twilio Account
1. Go to https://www.twilio.com/try-twilio
2. Sign up for a free account
3. Verify your email and phone number

### 2.2 Get WhatsApp Sandbox Access
1. Log in to Twilio Console
2. Navigate to **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Follow the instructions to join the sandbox:
   - Send a WhatsApp message to the Twilio number
   - Use the code provided (e.g., "join <your-code>")

### 2.3 Get Your Credentials
1. In Twilio Console, go to **Account** → **API keys & tokens**
2. Copy your:
   - **Account SID** (starts with AC...)
   - **Auth Token** (click to reveal)
3. Note your WhatsApp sandbox number (e.g., +1 415 523 8886)

---

## Step 3: Configure Your Application

### 3.1 Update Environment Variables

1. Open your `.env` file in the gym_management directory
2. Add/update these lines:

```env
# WhatsApp Configuration (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

**Replace with your actual values:**
- `TWILIO_ACCOUNT_SID`: Your Account SID from Twilio
- `TWILIO_AUTH_TOKEN`: Your Auth Token from Twilio
- `TWILIO_WHATSAPP_NUMBER`: Your WhatsApp sandbox number (keep the `whatsapp:` prefix)

### 3.2 For Test Mode (Option B)

Leave the values empty or use dummy values:

```env
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

The system will detect that WhatsApp is not configured and show a warning, but you can still test the interface.

---

## Step 4: Install Dependencies

```bash
# Make sure you're in the gym_management directory
cd d:\Python\gym_management

# Install Twilio library
pip install twilio>=8.0.0

# Or install all requirements
pip install -r requirements.txt
```

---

## Step 5: Add Phone Numbers to Members

### Important: Phone Number Field

Currently, the system looks for phone numbers in the member profile. You need to add a `phone_number` field to your models.

### Option 1: Add to MemberProfile Model

Edit `core/models.py` and add to the MemberProfile class:

```python
class MemberProfile(models.Model):
    # ... existing fields ...
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        help_text="Phone number with country code, e.g., +1234567890"
    )
```

Then run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Option 2: Add to CustomUser Model

Edit `core/models.py` and add to the CustomUser class:

```python
class CustomUser(AbstractUser):
    # ... existing fields ...
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        help_text="Phone number with country code, e.g., +1234567890"
    )
```

Then run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Phone Number Format

Always use international format:
- ✅ Correct: `+1234567890`
- ✅ Correct: `+919876543210`
- ❌ Wrong: `1234567890` (missing +)
- ❌ Wrong: `(123) 456-7890` (has formatting)

---

## Step 6: Test the Integration

### 6.1 Start the Server

```bash
python manage.py runserver
```

### 6.2 Access WhatsApp Messaging

1. Log in as Admin or Trainer
2. Go to Dashboard
3. Click on "WhatsApp Messages" tile
4. Or navigate to: http://localhost:8000/whatsapp/send/

### 6.3 Send a Test Message

1. Select a time slot or "All Members"
2. Type a test message:
   ```
   This is a test message from [Your Gym Name]. 
   If you receive this, WhatsApp integration is working!
   ```
3. Click "Send Message"
4. Confirm the action

### 6.4 Verify Delivery

**For Twilio (Option A):**
1. Check your WhatsApp on your phone
2. You should receive the message from the Twilio sandbox number
3. Check message history at: http://localhost:8000/whatsapp/history/

**For Test Mode (Option B):**
1. You'll see a warning that WhatsApp is not configured
2. Messages will be logged but not actually sent
3. Check message history to see the logged messages

---

## Step 7: Production Setup (Optional)

### For Production Use with Twilio:

1. **Upgrade Twilio Account**:
   - Move from sandbox to production
   - Request WhatsApp Business API access
   - Get a dedicated WhatsApp Business number

2. **Update Configuration**:
   - Replace sandbox number with your business number
   - Update `.env` with production credentials

3. **Opt-in Management**:
   - Ensure all members opt-in to receive messages
   - Implement opt-out functionality
   - Follow WhatsApp Business Policy

4. **Security**:
   - Never commit `.env` file to version control
   - Use environment variables in production
   - Rotate API tokens regularly

---

## Troubleshooting

### "WhatsApp service not configured"
**Solution**: 
- Check `.env` file has correct credentials
- Restart Django server after updating `.env`
- Verify credentials are not empty

### "No phone numbers found for members"
**Solution**:
- Add `phone_number` field to models (see Step 5)
- Add phone numbers to member profiles
- Ensure phone numbers are in international format (+...)

### Messages not sending
**Solution**:
- Check Twilio account balance
- Verify sandbox setup is complete
- Check Twilio logs for errors
- Ensure recipient has joined sandbox (for testing)

### Import Error: "No module named 'twilio'"
**Solution**:
```bash
pip install twilio>=8.0.0
```

---

## Next Steps

1. ✅ Add phone numbers to all member profiles
2. ✅ Test with a small group first
3. ✅ Create message templates for common announcements
4. ✅ Train staff on using the WhatsApp feature
5. ✅ Set up guidelines for message frequency and content

---

## Support Resources

- **Twilio Documentation**: https://www.twilio.com/docs/whatsapp
- **Twilio Support**: https://support.twilio.com
- **WhatsApp Business Policy**: https://www.whatsapp.com/legal/business-policy

---

## Cost Estimation

### Twilio WhatsApp Pricing (as of 2026)
- **Sandbox**: Free for testing
- **Production**: ~$0.005 - $0.02 per message (varies by country)
- **Monthly**: Estimate based on your usage:
  - 100 members × 4 messages/month = 400 messages
  - 400 × $0.01 = $4/month

Check current pricing: https://www.twilio.com/whatsapp/pricing

---

**Setup Complete!** 🎉

You're now ready to send WhatsApp messages to your gym members!
