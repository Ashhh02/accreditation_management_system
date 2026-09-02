import time

from django.core.cache import cache


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def hit_rate_limit(request, prefix, limit, window, identity=None):
    """Return True when the caller is over the fixed-window rate limit.

    `identity` defaults to the client IP; pass an extra value (e.g. the
    attempted username) when you want the limit keyed on more than the IP.
    Uses atomic increment where the cache backend supports it (Redis).
    """
    if identity is None:
        identity = client_ip(request)
    bucket = int(time.time()) // window
    key = f'ratelimit:{prefix}:{identity}:{bucket}'
    count = cache.get(key)
    if count is None:
        cache.set(key, 1, window)
        return False
    if count >= limit:
        return True
    try:
        new_count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return False
    return new_count > limit
