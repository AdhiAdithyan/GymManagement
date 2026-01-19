from rest_framework import permissions


class IsTenantUser(permissions.BasePermission):
    """Check if user belongs to request tenant"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admins can access any tenant
        if request.user.role == 'super_admin':
            return True
        
        # Check if user's tenant matches request tenant
        return request.user.tenant == request.tenant


class IsMember(permissions.BasePermission):
    """Check if user is a member"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'member'


class IsTrainer(permissions.BasePermission):
    """Check if user is a trainer or tenant admin"""
    
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['trainer', 'tenant_admin', 'super_admin'])


class IsTenantAdmin(permissions.BasePermission):
    """Check if user is a tenant admin"""
    
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['tenant_admin', 'super_admin'])


class IsSuperAdmin(permissions.BasePermission):
    """Check if user is a super admin (platform owner)"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'super_admin'
