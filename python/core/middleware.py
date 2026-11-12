import time
import uuid
from collections import defaultdict

from django.http import JsonResponse

from core.api.common import client_ip, err, setting, write_api_log

_HITS = defaultdict(list)


class PlatformMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.trace_id = uuid.uuid4().hex[:16]
        started = time.perf_counter()
        if request.path.startswith('/api/') and not self._ip_allowed(request):
            response = err('当前网络地址不在允许范围内', 403)
        elif request.path.startswith('/api/') and not self._rate_ok(request):
            response = err('请求过于频繁', 429)
        else:
            try:
                response = self.get_response(request)
            except Exception:
                response = JsonResponse({'ok': False, 'error': '服务器内部错误'}, status=500)
        response['X-Trace-Id'] = request.trace_id
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'same-origin'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        write_api_log(request, response, started)
        return response

    def _ip_allowed(self, request):
        mode = setting('ip_mode', 'off')
        raw = setting('ip_list', '')
        items = [item.strip() for item in raw.replace(',', '\n').splitlines() if item.strip()]
        if mode == 'off' or not items:
            return True
        ip = client_ip(request)
        listed = ip in items
        if mode == 'allow':
            return listed
        if mode == 'deny':
            return not listed
        return True

    def _rate_ok(self, request):
        limit = 20 if request.path.endswith('/login') else 180
        now = time.time()
        key = f'{client_ip(request)}:{request.path}'
        hits = [item for item in _HITS[key] if now - item < 60]
        if len(hits) >= limit:
            _HITS[key] = hits
            return False
        hits.append(now)
        _HITS[key] = hits
        return True
