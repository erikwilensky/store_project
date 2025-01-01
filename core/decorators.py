from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
import time
import logging

logger = logging.getLogger('core')


def rate_limit(requests=20, window=60):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get client IP
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))

            # Create unique cache key for this view and IP
            key = f'ratelimit:{view_func.__name__}:{ip}'

            # Get current request count and timestamp
            request_data = cache.get(key, {'count': 0, 'timestamp': time.time()})

            # Reset if window expired
            if time.time() - request_data['timestamp'] > window:
                request_data = {'count': 0, 'timestamp': time.time()}

            # Check rate limit
            if request_data['count'] >= requests:
                logger.warning(
                    'Rate limit exceeded for view %s by IP %s',
                    view_func.__name__,
                    ip
                )
                return JsonResponse({
                    'status': 'error',
                    'message': 'Rate limit exceeded for this endpoint'
                }, status=429)

            # Increment and store
            request_data['count'] += 1
            cache.set(key, request_data, window)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator