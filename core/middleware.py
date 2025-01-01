import time
import json
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger('core')


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all requests and their processing time."""

    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            log_data = {
                'path': request.path,
                'method': request.method,
                'status': response.status_code,
                'duration': round(duration * 1000, 2),  # Convert to milliseconds
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'ip': self.get_client_ip(request)
            }

            # Log additional info for errors
            if response.status_code >= 400:
                log_data['body'] = request.POST.dict() if request.method == 'POST' else None
                log_data['query_params'] = request.GET.dict()
                logger.error(f'Request failed: {json.dumps(log_data)}')
            else:
                logger.info(f'Request completed: {json.dumps(log_data)}')

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class RateLimitMiddleware(MiddlewareMixin):
    """Middleware to implement rate limiting on API endpoints."""

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.window = getattr(settings, 'RATE_LIMIT', {}).get('WINDOW', 60)
        self.max_requests = getattr(settings, 'RATE_LIMIT', {}).get('MAX_REQUESTS', 100)

    def process_request(self, request):
        # Skip rate limiting for non-API requests and admin
        if not request.path.startswith('/api/') or request.path.startswith('/admin/'):
            return None

        ip = self.get_client_ip(request)
        key = f'ratelimit:{ip}'

        # Get current request count and timestamp
        request_data = cache.get(key, {'count': 0, 'timestamp': time.time()})

        # Reset counter if window has expired
        if time.time() - request_data['timestamp'] > self.window:
            request_data = {'count': 0, 'timestamp': time.time()}

        # Increment request count
        request_data['count'] += 1

        # Store updated count and timestamp
        cache.set(key, request_data, self.window)

        # Check if rate limit exceeded
        if request_data['count'] > self.max_requests:
            logger.warning(
                'Rate limit exceeded for IP: %s, Path: %s',
                ip,
                request.path
            )
            return JsonResponse({
                'status': 'error',
                'message': 'Rate limit exceeded. Please try again later.',
                'retry_after': self.window
            }, status=429)

        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class ExceptionLoggingMiddleware(MiddlewareMixin):
    """Middleware to log unhandled exceptions."""

    def process_exception(self, request, exception):
        log_data = {
            'path': request.path,
            'method': request.method,
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'ip': self.get_client_ip(request),
            'exception_type': exception.__class__.__name__,
            'exception_message': str(exception)
        }

        if request.method == 'POST':
            log_data['post_data'] = request.POST.dict()
        if request.GET:
            log_data['query_params'] = request.GET.dict()

        logger.error(
            'Unhandled exception: %s',
            json.dumps(log_data),
            exc_info=True,
            extra={'request': request}
        )

        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class SessionMaintenanceMiddleware(MiddlewareMixin):
    """Middleware to handle session maintenance and cleanup."""

    def process_request(self, request):
        # Refresh session timeout
        if request.user.is_authenticated:
            request.session.modified = True

        # Clean up expired sessions periodically
        if hasattr(request, 'session') and 'last_cleanup' not in request.session:
            from django.core.management import call_command
            call_command('clearsessions')
            request.session['last_cleanup'] = time.time()


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add security headers to responses."""

    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Add CSP header in non-debug mode
        if not settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data:; "
                "font-src 'self' data:; "
                "frame-ancestors 'none'"
            )
            response['Content-Security-Policy'] = csp

        return response