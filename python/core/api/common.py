import json
import time
from functools import wraps

from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from core.models import ApiLog, OperationLog, Session, Setting


def ok(**payload):
    return JsonResponse({'ok': True, **payload}, json_dumps_params={'ensure_ascii': False})


def err(message, status=400):
    return JsonResponse({'ok': False, 'error': message}, status=status, json_dumps_params={'ensure_ascii': False})


def body(request):
    if not request.body:
        return {}
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def setting(key, default=''):
    row = Setting.objects.filter(key=key).first()
    return row.value if row else default


def setting_int(key, default):
    try:
        return int(setting(key, default))
    except (TypeError, ValueError):
        return default


def paginate(request, qs):
    try:
        page = max(int(request.GET.get('page') or 1), 1)
        size = min(max(int(request.GET.get('page_size') or 10), 1), 200)
    except ValueError:
        page, size = 1, 10
    total = qs.count()
    start = (page - 1) * size
    return total, list(qs[start:start + size])


def search(qs, keyword, fields):
    keyword = (keyword or '').strip()
    if not keyword or not fields:
        return qs
    query = Q()
    for field in fields:
        query |= Q(**{f'{field}__icontains': keyword})
    return qs.filter(query)


def log_op(request, action, target='', detail=''):
    account = getattr(request, 'account', None)
    OperationLog.objects.create(
        account=account,
        action=action,
        target=target,
        detail=str(detail)[:2000],
        ip=client_ip(request),
    )


def current_session(request):
    header = request.headers.get('Authorization', '')
    token = ''
    if header.startswith('Bearer '):
        token = header[7:].strip()
    if not token:
        token = (request.GET.get('token') or '').strip()
    if not token:
        return None
    now = timezone.now()
    session = Session.objects.select_related('account').filter(access_token=token, revoked=False).first()
    if session is None or session.access_expires <= now:
        return None
    if session.account.is_deleted or session.account.status != 'active':
        return None
    return session


def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        session = current_session(request)
        if session is None:
            return err('未登录或登录已失效', 401)
        request.session_row = session
        request.account = session.account
        return view(request, *args, **kwargs)

    return wrapper


def super_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.account.is_super:
            return err('没有权限', 403)
        return view(request, *args, **kwargs)

    return wrapper


_SEEN = {}


def idempotent(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        key = request.headers.get('Idempotency-Key', '').strip()
        if key:
            now = time.time()
            hit = _SEEN.get(key)
            if hit and now - hit < 60:
                return err('请勿重复提交', 409)
            _SEEN[key] = now
            if len(_SEEN) > 500:
                for item in list(_SEEN)[:200]:
                    _SEEN.pop(item, None)
        return view(request, *args, **kwargs)

    return wrapper


def write_api_log(request, response, started):
    path = request.path
    if not path.startswith('/api/') or path.endswith('/api/logs'):
        return
    try:
        ApiLog.objects.create(
            trace_id=getattr(request, 'trace_id', ''),
            method=request.method,
            path=path[:255],
            status_code=getattr(response, 'status_code', 0),
            duration_ms=int((time.perf_counter() - started) * 1000),
            ip=client_ip(request),
        )
    except Exception:
        return
