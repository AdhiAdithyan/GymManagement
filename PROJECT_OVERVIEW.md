# Gym Management System - Project Overview

## 1. Executive Summary
This project is a robust, multi-tenant **Gym Management System** built with **Django**. It is designed to service multiple gyms (tenants) simultaneously, allowing each to have its own branding, members, staff, and financial data isolation. The system provides web interfaces for Administrators, Trainers, and Members, alongside a REST API for potential mobile or external integrations.

## 2. System Architecture

The project is structured into three primary Django applications:

### 2.1 Core App (`core`)
Handles the foundational data models and authentication.
- **Tenant**: Manages multi-tenancy, subdomains, and subscription plans for gym owners.
- **CustomUser**: Extends the default Django user to include roles (`super_admin`, `tenant_admin`, `trainer`, `member`, `staff`) and tenant association.
- **MemberProfile**: Detailed profile for gym members, including membership type, physical details, and phone numbers.
- **BrandingConfig**: Allows tenants to white-label the application with custom logos, colors, and app infrastructure.
- **Utility Models**: `Attendance`, `Payment`, `Expense`, `AuditLog`, `WhatsAppMessage`.

### 2.2 Gym App (`gym`)
Contains the business logic and user-facing views (MVT pattern).
- **Dashboards**: Role-specific dashboards for Admins, Trainers, and Members.
- **Management**: Views for adding/editing members, marking attendance, and handling payments.
- **Communication**: Integrated WhatsApp messaging for bulk reminders and alerts; Internal chat rooms.
- **Content Delivery**: Workout video uploads and diet plan assignments.
- **Reporting**: Financial overview, PDF report generation, and graphs.

### 2.3 API App (`api`)
Provides a RESTful interface using **Django Rest Framework (DRF)**.
- Includes comprehensive documentation via **drf-spectacular** (Swagger UI).
- Exposes endpoints for identifying tenants/roles and managing resources programmatically.

---

## 3. Key Features

### User Roles & Permissions
- **Super Admin**: Platform owner, manages tenants.
- **Tenant Admin**: Gym owner, full access to their gym's data.
- **Trainer**: Can manage schedules, assign diets, upload videos, and view member attendance.
- **Member**: Access to personal dashboard, payment history, attendance logs, and assigned content.

### Membership & Finance
- **Subscriptions**: Tracks monthly/yearly plans with auto-renewal status.
- **Payments**: Records registration and monthly fees; generates financial reports (Income vs. Expense).
- **PDF Reports**: Exportable comprehensive reports for business analysis.

### Operational Tools
- **Attendance**: Daily check-in system with history tracking.
- **Leave Management**: Workflow for members to request leave and admins/trainers to approve/reject.
- **WhatsApp Integration**: automated or manual messaging for payment reminders and announcements.
- **Bulk Import**: CSV import functionality for quickly onboarding member phone numbers.

### Content Management
- **Video Library**: Trainers can upload workout videos targetting specific audience levels.
- **Diet Plans**: Personalized diet text blocks assigned to members.

---

## 4. Codebase Validation & Observations

### 4.1 Structure Quality
- **Modular Design**: The separation of `core` (data) and `gym` (logic) is well-maintained, preventing circular dependencies.
- **Model Completeness**: The data schema is rich, covering edge cases like 'Paused' subscriptions, 'Leave' requests, and 'Audit Logs'.
- **Security**: 
  - `login_required` decorators are used extensively.
  - Role-based checks exist within views (e.g., `if user.role not in [...]`).

### 4.2 Areas for Potential Improvement
1.  **URL Configuration**: In `gym_management/urls.py`, the static/media file serving logic for `DEBUG` mode is duplicated. This is functional but redundant.
2.  **Data Normalization**: 
    - `MemberProfile` contains `membership_type`, `monthly_amount`, and `next_payment_date`.
    - There is also a `Subscription` model with `plan`, `amount`, `start_date`, and `end_date`.
    - **Recommendation**: Ensure the system fully transitions to using the `Subscription` model to handle history and renewals, reducing reliance on the flat fields in `MemberProfile` to avoid data desynchronization.
3.  **Role Decorators**: Currently, permissions are checked manually inside views (e.g., `if user.role != 'admin': redirect`). Implementing custom decorators like `@role_required('trainer')` would clean up `views.py` and reduce code duplication.
4.  **Phone Validation**: Phone numbers are validated in the `clean()` method of `MemberProfile`. Ensure this validation is consistently invoked in all forms and API serializers, including the bulk import logic (which currently keeps its own validation logic).

---

## 5. Technology Stack
- **Backend Frameork**: Django 5.x
- **API Framework**: Django Rest Framework (DRF)
- **Database**: SQLite (Development) / Configurable for PostgreSQL
- **Frontend**: Django Templates + Vanilla CSS / Bootstrap (implied)
- **PDF Generation**: `xhtml2pdf`
- **Utilities**: `fd` (File finding), `ripgrep` (Search) - *dev tools*

This overview confirms the application is in a mature state with a comprehensive feature set suitable for gym management usage.
