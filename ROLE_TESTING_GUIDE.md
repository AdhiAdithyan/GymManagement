# Role-Based Access Control - Testing Guide

## Overview
This document provides a comprehensive guide to test all role-based workflows in the Gym Management System.

## Test Users

All test users have been created with the password: **demo123**

| Username | Role | Email | Description |
|----------|------|-------|-------------|
| superadmin | Super Admin | superadmin@platform.com | Platform owner with unrestricted access |
| demoadmin | Tenant Admin | admin@demo.com | Gym owner/administrator |
| demotrainer | Trainer | trainer@demo.com | Gym trainer |
| demomember | Member | member@demo.com | Gym member |
| demostaff | Staff | staff@demo.com | Gym staff |

## Role Permissions Matrix

### Super Admin
**Full Platform Access**
- ✓ Can access all tenants
- ✓ Can create/manage tenants
- ✓ Can manage all users across tenants
- ✓ Has unrestricted access to all features
- ✓ Bypasses all role checks

### Tenant Admin (Gym Owner)
**Gym Management**
- ✓ Can add/edit/delete members
- ✓ Can manage trainers
- ✓ Can view financial reports
- ✓ Can send WhatsApp messages to members
- ✓ Can mark attendance
- ✓ Can approve/reject leave requests
- ✓ Can manage branding settings
- ✓ Can bulk import phone numbers
- ✓ Can generate reports and export PDFs

### Trainer
**Training & Member Management**
- ✓ Can view member list
- ✓ Can mark attendance
- ✓ Can upload workout videos
- ✓ Can create diet plans for members
- ✓ Can request leave
- ✓ Can view member attendance history

### Member
**Self-Service Portal**
- ✓ Can view own attendance history
- ✓ Can view own payment history
- ✓ Can view workout videos
- ✓ Can view assigned diet plans
- ✓ Can request leave
- ✓ Can access QR code for attendance scanning

### Staff
**Basic Operations**
- ✓ Can view member list
- ✓ Can mark attendance

---

## Test Scenarios

### 1. Super Admin Testing

#### Login
1. Navigate to `/login`
2. Username: `superadmin`
3. Password: `demo123`
4. Should redirect to admin dashboard

#### Test Cases
- [ ] Access admin dashboard
- [ ] View all tenants
- [ ] Access any tenant's data
- [ ] Manage users across tenants
- [ ] All features should be accessible

---

### 2. Tenant Admin Testing

#### Login
1. Navigate to `/login`
2. Username: `demoadmin`
3. Password: `demo123`
4. Should redirect to admin dashboard

#### Test Cases

**Member Management**
- [ ] Navigate to `/gym/members/`
- [ ] View member list with filters
- [ ] Click "Add Member" button
- [ ] Fill out member form and submit
- [ ] Edit an existing member
- [ ] Delete a member (should show confirmation)

**Attendance Management**
- [ ] Navigate to `/gym/mark-attendance/`
- [ ] View attendance list
- [ ] Mark attendance for members
- [ ] Filter by date and time slot
- [ ] Use QR code scanner (Quick Scan feature)

**Financial Reports**
- [ ] Navigate to `/gym/finance/`
- [ ] View income/expense summary
- [ ] Filter by date range
- [ ] View payment history
- [ ] Add expense entries

**WhatsApp Messaging**
- [ ] Navigate to `/gym/send-whatsapp/`
- [ ] Select time slot
- [ ] Compose message
- [ ] Send to selected members
- [ ] View message history at `/gym/whatsapp-history/`

**Leave Management**
- [ ] Navigate to `/gym/leave-requests/`
- [ ] View pending leave requests
- [ ] Approve a leave request
- [ ] Reject a leave request with reason

**Reports & Analytics**
- [ ] Navigate to `/gym/reports/`
- [ ] View attendance analytics
- [ ] View revenue charts
- [ ] Export PDF report

**Bulk Operations**
- [ ] Navigate to `/gym/bulk-import-phones/`
- [ ] Download sample CSV
- [ ] Upload CSV with phone numbers
- [ ] Verify import success

---

### 3. Trainer Testing

#### Login
1. Navigate to `/login`
2. Username: `demotrainer`
3. Password: `demo123`
4. Should redirect to trainer dashboard

#### Test Cases

**Dashboard**
- [ ] View trainer dashboard
- [ ] See today's schedule
- [ ] View assigned members

**Member Management**
- [ ] Navigate to `/gym/members/`
- [ ] View member list (read-only)
- [ ] Should NOT see "Add Member" button
- [ ] Should NOT see "Delete" buttons

**Attendance**
- [ ] Navigate to `/gym/trainer-attendance/`
- [ ] Mark attendance for members
- [ ] View attendance history

**Workout Videos**
- [ ] Navigate to `/gym/upload-video/`
- [ ] Upload a workout video
- [ ] Add title and description
- [ ] Set target audience (all/beginner/advanced)

**Diet Plans**
- [ ] Navigate to `/gym/create-diet-plan/`
- [ ] Select a member
- [ ] Create diet plan with title and content
- [ ] Submit and verify

**Leave Requests**
- [ ] Navigate to `/gym/leave-request/create/`
- [ ] Fill leave request form
- [ ] Submit request
- [ ] Should appear in admin's pending requests

**Restricted Access**
- [ ] Try to access `/gym/finance/` - should redirect to dashboard
- [ ] Try to access `/gym/send-whatsapp/` - should redirect to dashboard
- [ ] Try to access `/gym/add-member/` - should redirect to dashboard

---

### 4. Member Testing

#### Login
1. Navigate to `/login`
2. Username: `demomember`
3. Password: `demo123`
4. Should redirect to member dashboard

#### Test Cases

**Dashboard**
- [ ] View member dashboard
- [ ] See payment due alerts (if applicable)
- [ ] View attendance statistics

**Attendance History**
- [ ] Navigate to `/gym/member/attendance/`
- [ ] View own attendance records
- [ ] Filter by date range
- [ ] Pagination should work

**Payment History**
- [ ] Navigate to `/gym/member/payments/`
- [ ] View payment records
- [ ] See payment types and amounts
- [ ] Filter by date range

**Workout Videos**
- [ ] Navigate to `/gym/member/videos/`
- [ ] View available workout videos
- [ ] Filter by target audience
- [ ] Play videos

**Diet Plans**
- [ ] Navigate to `/gym/member/diet/`
- [ ] View assigned diet plans
- [ ] See diet plan details

**QR Code**
- [ ] Navigate to `/gym/member-qr/`
- [ ] View personal QR code
- [ ] QR code should be scannable

**Leave Requests**
- [ ] Navigate to `/gym/leave-request/create/`
- [ ] Submit leave request
- [ ] View request status

**Restricted Access**
- [ ] Try to access `/gym/members/` - should redirect to dashboard
- [ ] Try to access `/gym/finance/` - should redirect to dashboard
- [ ] Try to access `/gym/mark-attendance/` - should redirect to dashboard
- [ ] Try to access other members' data - should be blocked

---

### 5. Staff Testing

#### Login
1. Navigate to `/login`
2. Username: `demostaff`
3. Password: `demo123`
4. Should redirect to dashboard

#### Test Cases

**Member List**
- [ ] Navigate to `/gym/members/`
- [ ] View member list (read-only)
- [ ] Should NOT see "Add Member" button
- [ ] Should NOT see "Edit" or "Delete" buttons

**Attendance**
- [ ] Navigate to `/gym/mark-attendance/`
- [ ] Mark attendance for members
- [ ] Use QR scanner if available

**Restricted Access**
- [ ] Try to access `/gym/finance/` - should redirect
- [ ] Try to access `/gym/send-whatsapp/` - should redirect
- [ ] Try to access `/gym/upload-video/` - should redirect
- [ ] Try to access `/gym/create-diet-plan/` - should redirect

---

## Cross-Role Testing

### Access Control Validation
Test that users cannot access features outside their role:

1. **Member trying to access admin features**
   - Direct URL access to `/gym/add-member/` should redirect
   - Direct URL access to `/gym/finance/` should redirect

2. **Trainer trying to access admin features**
   - Direct URL access to `/gym/finance/` should redirect
   - Direct URL access to `/gym/send-whatsapp/` should redirect

3. **Staff trying to access management features**
   - Direct URL access to `/gym/add-member/` should redirect
   - Direct URL access to `/gym/upload-video/` should redirect

### Tenant Isolation
1. Create a second tenant (if super admin)
2. Verify users can only see data from their own tenant
3. Verify cross-tenant data leakage is prevented

---

## API Testing (if applicable)

### API Endpoints
Test API access with different roles:

1. **Member API** (`/api/member/`)
   - Should require member role
   - Should only return own data

2. **Trainer API** (`/api/trainer/`)
   - Should require trainer role or higher
   - Should return appropriate data

3. **Admin API** (`/api/admin/`)
   - Should require tenant_admin role or higher
   - Should return tenant-specific data

---

## Common Issues to Check

### Authentication
- [ ] Unauthenticated users redirected to login
- [ ] Session persistence works correctly
- [ ] Logout works and clears session

### Authorization
- [ ] Role-based redirects work correctly
- [ ] Error messages are user-friendly
- [ ] No sensitive data exposed in error messages

### Data Integrity
- [ ] Users can only modify their own tenant's data
- [ ] Cascade deletes work correctly
- [ ] Foreign key constraints are enforced

### UI/UX
- [ ] Navigation menus show only allowed features
- [ ] Buttons/links for restricted features are hidden
- [ ] Forms validate correctly
- [ ] Success/error messages display properly

---

## Automated Testing

Run the validation script:
```bash
python validate_roles.py
```

This script will:
1. Validate all users have correct roles and tenants
2. Create missing test users
3. Check view decorators
4. Verify permission structure
5. Generate a comprehensive report

---

## Reporting Issues

When reporting issues, include:
1. **User Role**: Which test user you were logged in as
2. **URL**: The page where the issue occurred
3. **Expected Behavior**: What should have happened
4. **Actual Behavior**: What actually happened
5. **Steps to Reproduce**: Detailed steps to recreate the issue
6. **Screenshots**: If applicable

---

## Success Criteria

All tests pass when:
- ✓ Each role can access only their permitted features
- ✓ Unauthorized access attempts are properly blocked
- ✓ No data leakage between tenants
- ✓ All workflows complete successfully
- ✓ No errors in console or logs
- ✓ UI shows appropriate options for each role

---

## Next Steps After Testing

1. **Document any bugs found** in a separate issue tracker
2. **Update this guide** if new features are added
3. **Create automated tests** for critical workflows
4. **Set up CI/CD** to run tests on every commit
5. **Monitor production** for role-based access violations

---

## Support

For questions or issues:
- Check the validation script output
- Review the `core/decorators.py` file for role logic
- Check `api/permissions.py` for API permissions
- Review view decorators in `gym/views.py`
