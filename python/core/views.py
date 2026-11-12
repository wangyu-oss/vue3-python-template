import json
import secrets
from functools import wraps

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Account, Note
from .passwords import hash_password, verify_password


def _body(request):
    if not request.body:
        return {}
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _error(message, status=400):
    return JsonResponse({'ok': False, 'error': message}, status=status)


def _ok(**payload):
    return JsonResponse({'ok': True, **payload})


def _account_from_request(request):
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    token = header[7:].strip()
    if not token:
        return None
    return Account.objects.filter(token=token).first()


def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        account = _account_from_request(request)
        if account is None:
            return _error('未登录或登录已失效', 401)
        request.account = account
        return view(request, *args, **kwargs)

    return wrapper


@require_http_methods(['GET'])
def health(request):
    return _ok(service='vue3-python-template', database='data/app.sqlite3')


@require_http_methods(['POST'])
def login(request):
    data = _body(request)
    if data is None:
        return _error('请求格式不正确')
    username = str(data.get('username') or '').strip()
    password = str(data.get('password') or '')
    account = Account.objects.filter(username=username).first()
    if account is None or not verify_password(password, account.password):
        return _error('用户名或密码错误', 401)
    account.token = secrets.token_hex(24)
    account.save(update_fields=['token'])
    return _ok(token=account.token, user=account.public())


@require_http_methods(['GET'])
@login_required
def me(request):
    return _ok(user=request.account.public())


@require_http_methods(['POST'])
@login_required
def profile(request):
    data = _body(request)
    if data is None:
        return _error('请求格式不正确')
    display_name = str(data.get('display_name') or '').strip()
    if not display_name:
        return _error('请填写显示名称')
    if len(display_name) > 64:
        return _error('显示名称不能超过 64 个字符')
    request.account.display_name = display_name
    request.account.save(update_fields=['display_name'])
    return _ok(user=request.account.public())


@require_http_methods(['POST'])
@login_required
def password(request):
    data = _body(request)
    if data is None:
        return _error('请求格式不正确')
    old_password = str(data.get('old_password') or '')
    new_password = str(data.get('new_password') or '')
    if not verify_password(old_password, request.account.password):
        return _error('当前密码不正确')
    if len(new_password) < 6:
        return _error('新密码至少 6 位')
    request.account.password = hash_password(new_password)
    request.account.token = secrets.token_hex(24)
    request.account.save(update_fields=['password', 'token'])
    return _ok(token=request.account.token, user=request.account.public())


@require_http_methods(['GET'])
@login_required
def summary(request):
    return _ok(
        user=request.account.public(),
        note_count=Note.objects.count(),
        database='data/app.sqlite3',
    )


@require_http_methods(['GET'])
@login_required
def notes(request):
    return _ok(items=[item.public() for item in Note.objects.all()])


@require_http_methods(['POST'])
@login_required
def note_save(request):
    data = _body(request)
    if data is None:
        return _error('请求格式不正确')
    title = str(data.get('title') or '').strip()
    content = str(data.get('content') or '').strip()
    if not title:
        return _error('请填写标题')
    if len(title) > 120:
        return _error('标题不能超过 120 个字符')
    note_id = data.get('id')
    if note_id:
        note = Note.objects.filter(id=note_id).first()
        if note is None:
            return _error('笔记不存在', 404)
        note.title = title
        note.content = content
        note.save(update_fields=['title', 'content', 'updated_at'])
    else:
        note = Note.objects.create(title=title, content=content)
    return _ok(item=note.public())


@require_http_methods(['POST'])
@login_required
def note_delete(request):
    data = _body(request)
    if data is None:
        return _error('请求格式不正确')
    note = Note.objects.filter(id=data.get('id')).first()
    if note is None:
        return _error('笔记不存在', 404)
    note.delete()
    return _ok()
