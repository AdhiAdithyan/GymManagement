# 📄 Gym Management System - Technical Documentation

This document provides a comprehensive overview of the system architecture, database models, and functional modules of the Gym Management System.

---

## 🏗 System Architecture

The application is built using a **Modular Monolith** architecture with Django. It supports **Multi-Tenancy** at the database level using a `Tenant` foreign key on all core entities.

### **Core Packages**
*   `core`: Contains the base models, multi-tenancy logic, and shared utilities.
*   `gym`: Contains the business logic, views, forms, and templates for the gym portal.
*   `api`: (Optional) REST API endpoints for mobile integration.

---

## 🗄 Database Models (High-Level)

### **1. Identity & Access**
*   **Tenant**: Represents a gym organization. Stores subdomain, branding, and contact info.
*   **CustomUser**: Extended Django User model with `role` (Admin, Trainer, Member, Staff) and `tenant` association.
*   **BrandingConfig**: Stores visual preferences (colors, logos) and feature toggles (WhatsApp auto-reminders) for each tenant.

### **2. Member Management**
*   **MemberProfile**: Stores member-specific data:
    *   `membership_type`: Monthly, Quarterly, Yearly.
    *   `allotted_slot`: Managed training windows.
    *   `phone_number`: Validated international format for WhatsApp integration.
    *   `next_payment_date`: Automatically tracked for notification logic.

### **3. Financials**
*   **Payment**: Records all income. Supports `registration` and `monthly` types with custom date entries for physical tracking.
*   **Expense**: Records gym outflows. Filterable by category (Salary, Maintenance, etc.).

### **4. Notifications & Communication**
*   **WhatsAppMessage**: Logs every outgoing message. Tracks:
    *   `time_slot`: Targeted group or 'all'.
    *   `status`: sent, failed, pending.
    *   `error_message`: For troubleshooting API failures.

---

## 🛠 Key Functional Modules

### **1. WhatsApp Automation Service (`gym/whatsapp_service.py`)**
A service class that wraps the Twilio API.
*   **Validation**: Ensures phone numbers are E.164 compliant.
*   **Integration**: Connects to the `send_payment_reminders` command to execute background notifications.

### **2. Finance Hub**
A comprehensive dashboard (`/finance/`) that performs real-time aggregation:
*   **Revenue**: `Sum('amount')` from `Payment` model.
*   **Expenses**: `Sum('amount')` from `Expense` model.
*   **Profit**: Calculated difference with customizable date window filtering.

### **3. Bulk Import Engine**
Handles high-volume data entry using Python's `csv` and `io` libraries:
*   **Atomic Transactions**: Uses `transaction.atomic()` to ensure data integrity—if one row fails, the entire batch is rolled back or error-logged without corrupting the database.
*   **User Provisioning**: Automatically creates `CustomUser` accounts and password hashing for every imported member.

---

## 🚦 Application Logic Flows

### **Payment Reminder Flow**
1.  **Trigger**: `python manage.py send_payment_reminders` runs (daily).
2.  **Lookup**: Queries `BrandingConfig` for tenants with `enable_auto_whatsapp_reminders=True`.
3.  **Calculation**: Identifies members due in **X days** (tenant settings), **Due Today**, or **Overdue**.
4.  **Anti-Spam**: Checks `WhatsAppMessage` logs for any message sent to the member in the last 24 hours.
5.  **Execution**: Calls `whatsapp_service.send_message()` and logs the result.

---

## 📁 Directory Structure
```text
gym_management/
├── core/                   # Shared platform logic
│   ├── management/         # Background commands
│   ├── migrations/         # DB History
│   └── models.py           # Core Schema
├── gym/                    # Business Logic
│   ├── forms.py            # Custom UI Forms
│   ├── views.py            # Request Handlers
│   └── whatsapp_service.py # Messaging Logic
├── templates/              # UI Layer
│   └── gym/                # Module-specific templates
└── static/                 # CSS/JS/Assets
```

---

## 👨‍💻 Developer Notes
*   **Security**: Always use the `@role_required` decorator for administrative views.
*   **Branding**: Use CSS variables (e.g., `var(--primary-color)`) in templates to ensure tenant-specific colors are applied.
*   **CSV Import**: Column headers must match the sample provided in `download_member_import_sample`.

---
**Standard**: ISO/IEC 25010 Software Quality Model compliant.
