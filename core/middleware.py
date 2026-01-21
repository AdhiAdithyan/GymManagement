from django.utils.deprecation import MiddlewareMixin
from core.models import Tenant
from django.http import JsonResponse


class TenantMiddleware(MiddlewareMixin):
    """Isolate requests by tenant based on subdomain or header"""
    
    def process_request(self, request):
        # Skip for admin, static files, and auth endpoints
        if (request.path.startswith('/admin/') or 
            request.path.startswith('/static/') or
            request.path.startswith('/media/')):
            return None
        
        tenant = None
        
        # Try to get tenant from subdomain
        host = request.get_host().split(':')[0]
        subdomain_parts = host.split('.')
        
        # If we have a subdomain (more than 2 parts like subdomain.domain.com)
        if len(subdomain_parts) > 2 or (len(subdomain_parts) == 2 and subdomain_parts[0] != 'www'):
            subdomain = subdomain_parts[0]
            
            if subdomain and subdomain != 'www':
                try:
                    tenant = Tenant.objects.filter(subdomain=subdomain, is_active=True).first()
                except Exception:
                    # Gracefully handle missing table or other DB errors
                    pass
        
        # Fallback: Try X-Tenant-ID header (for development/testing/mobile apps)
        if not tenant:
            tenant_id = request.headers.get('X-Tenant-ID') or request.headers.get('X-TENANT-ID')
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=int(tenant_id), is_active=True)
                except (Tenant.DoesNotExist, ValueError):
                    pass
        
        # Fallback: Try to get tenant from authenticated user
        if not tenant and request.user.is_authenticated and hasattr(request.user, 'tenant'):
            tenant = request.user.tenant
        
        # Store tenant in request
        request.tenant = tenant
        
        # For API endpoints, enforce tenant requirement
        if request.path.startswith('/api/') and not request.path.startswith('/api/auth/'):
            if not tenant:
                return JsonResponse({
                    'error': 'Tenant not found',
                    'detail': 'Please provide X-Tenant-ID header or use tenant-specific subdomain'
                }, status=400)
        
        return None
