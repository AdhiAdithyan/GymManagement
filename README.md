# Gym Management System (v3.5.0)

A comprehensive, multi-tenant enabled Gym Management System built with Django, designed for visual excellence and automated operations.

## 🚀 Key Modules & Features

### 1. **Administrative & Multi-Tenant Support**
*   **Multi-Tenancy**: Support for multiple gyms (tenants) under a single platform.
*   **White-Labeling**: Custom gym names, colors (Primary, Secondary, Accent), and logos per tenant.
*   **Dashboard**: Premium analytics dashboard for Admins, Trainers, and Members.
*   **Role-Based Access (RBAC)**: Distinct permissions for Super Admins, Tenant Admins, Trainers, and Members.

### 2. **Finance & Payment Management**
*   **Finance Hub**: A centralized portal for tracking the gym's financial health.
*   **Manual Payments**: Record physical/cash payments with ease.
*   **Expense Tracking**: Categorized expense logging (Maintenance, Salary, Electricity, etc.).
*   **Automated Billing**: Logic for tracking registration fees and monthly subscriptions.
*   **Reporting**: Export detailed financial reports to PDF.

### 3. **WhatsApp Automation Engine**
*   **Auto-Reminders**: Smart payment reminders sent via WhatsApp based on due dates.
*   **Configurable Scheduling**: Set reminders to go out 1-30 days before the due date.
*   **Smart Logic**: Automatically handles "Due Today" and "Overdue" notifications with varying levels of urgency.
*   **Group Messaging**: Send WhatsApp messages to members based on their training time slots.
*   **History Logs**: Full tracking of sent messages, delivery status, and system-generated notifications.

### 4. **Member Operations**
*   **Bulk Onboarding**: Import hundreds of members in seconds via CSV.
*   **Sample CSV Service**: Downloadable template to ensure error-free data entry.
*   **Attendance System**: QR code scanning support and multiple daily check-ins for morning/evening sessions.
*   **Photo Identification**: Visual profile management with initials-based fallbacks.
*   **Diet & Workout Plans**: AI-integrated plan generation and manual assignment by trainers.

### 5. **Staff & Facility Management**
*   **Staff Directory**: Manage cleaning and maintenance staff separately from trainers.
*   **Leave Management**: Dedicated system for approval/rejection of staff leave requests.

---

## 🛠 Tech Stack
*   **Backend**: Django 4.x (Python)
*   **Database**: PostgreSQL / SQLite
*   **Frontend**: Vanilla CSS (Custom UI Components), HTML5, JavaScript (HTMX for dynamic updates)
*   **Messaging**: Twilio WhatsApp API Integration
*   **Reporting**: xhtml2pdf for document generation
*   **Icons**: FontAwesome 6+

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/AdhiAdithyan/GymManagement.git
cd gym_management
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///db.sqlite3
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+123456789
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Run Server
```bash
python manage.py runserver
```

---

## 🕒 Automation (Cron Jobs)
To enable automatic WhatsApp payment reminders, set up a daily task to run:
```bash
python manage.py send_payment_reminders
```

---

## 🧪 Testing
The project includes a comprehensive test suite for navigation and RBAC:
```bash
python manage.py test gym.navigation_tests
```

## 📄 License
Custom Enterprise License. All rights reserved (2026).