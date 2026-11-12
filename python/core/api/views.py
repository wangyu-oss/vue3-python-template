import json
import secrets
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.api.common import body, client_ip, err, idempotent, log_op, login_required, ok, paginate, search, setting, setting_int
from core.captcha import check as check_captcha
from core.captcha import issue as issue_captcha
from core.jobs import execute
from core.models import (
    Account,
    Announcement,
    ApiLog,
    Approval,
    Department,
    DictItem,
    DictType,
    Favorite,
    FeatureFlag,
    Job,
    LoginLog,
    Menu,
    Message,
    Note,
    OperationLog,
    Post,
    RecycleItem,
    Role,
    SerialRule,
    Session,
    Setting,
    StoredFile,
    Todo,
)
from core.passwords import hash_password, verify_password

UPLOAD_DIR = Path(settings.DATA_DIR) if hasattr(settings, 'DATA_DIR') else Path(settings.BASE_DIR).parent / 'data'
UPLOAD_DIR = Path(settings.BASE_DIR).parent / 'data' / 'uploads'


def _mask_phone(value):
    text = value or ''
    if len(text) < 7:
        return text
    return text[:3] + '****' + text[-4:]


def _permissions(account):
    if account.is_super:
        return list(Menu.objects.exclude(permission='').values_list('permission', flat=True))
    return list(
        Menu.objects.filter(roles__accounts=account).exclude(permission='').values_list('permission', flat=True).distinct()
    )


def _menu_tree(account):
    if account.is_super:
        rows = Menu.objects.filter(menu_type__in=['dir', 'menu'])
    else:
        rows = Menu.objects.filter(menu_type__in=['dir', 'menu'], roles__accounts=account).distinct()
    nodes = [row.public() for row in rows if row.visible or row.menu_type == 'dir']
    by_parent = {}
    for node in nodes:
        by_parent.setdefault(node['parent_id'], []).append(node)
    def build(parent_id):
        children = by_parent.get(parent_id, [])
        for child in children:
            child['children'] = build(child['id'])
        return children
    return build(None)


def _issue_session(request, account, remember):
    if setting('allow_multi_login', 'yes') != 'yes':
        Session.objects.filter(account=account, revoked=False).update(revoked=True)
    now = timezone.now()
    access_minutes = setting_int('session_minutes', 120)
    refresh_days = 30 if remember else 7
    session = Session.objects.create(
        account=account,
        access_token=secrets.token_hex(24),
        refresh_token=secrets.token_hex(24),
        ip=client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        access_expires=now + timedelta(minutes=access_minutes),
        refresh_expires=now + timedelta(days=refresh_days),
    )
    return session


def _auth_payload(account, session):
    return {
        'token': session.access_token,
        'refresh_token': session.refresh_token,
        'user': account.public(),
        'permissions': _permissions(account),
        'menus': _menu_tree(account),
    }


@require_http_methods(['GET'])
def health(request):
    return ok(service='vue3-python-template', database='data/app.sqlite3')


@require_http_methods(['GET'])
def captcha(request):
    cid, svg = issue_captcha()
    return ok(captcha_id=cid, svg=svg)


@require_http_methods(['POST'])
def login(request):
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    if setting('login_captcha', 'no') == 'yes' and not check_captcha(data.get('captcha_id'), data.get('captcha_code')):
        return err('验证码不正确')
    username = str(data.get('username') or '').strip()
    password = str(data.get('password') or '')
    account = Account.objects.filter(username=username, is_deleted=False).first()
    if account and account.locked_until and account.locked_until > timezone.now():
        LoginLog.objects.create(username=username, ip=client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', '')[:255], success=False, message='账号已锁定')
        return err('账号已锁定，请稍后再试', 423)
    if account is None or account.status != 'active' or not verify_password(password, account.password):
        if account:
            account.failed_logins += 1
            limit = setting_int('login_fail_limit', 5)
            if account.failed_logins >= limit:
                account.locked_until = timezone.now() + timedelta(minutes=setting_int('lock_minutes', 15))
                account.failed_logins = 0
            account.save(update_fields=['failed_logins', 'locked_until'])
        LoginLog.objects.create(username=username, ip=client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', '')[:255], success=False, message='用户名或密码错误')
        return err('用户名或密码错误', 401)
    account.failed_logins = 0
    account.locked_until = None
    account.save(update_fields=['failed_logins', 'locked_until'])
    session = _issue_session(request, account, bool(data.get('remember')))
    LoginLog.objects.create(username=username, ip=client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', '')[:255], success=True, message='登录成功')
    return ok(**_auth_payload(account, session))


@require_http_methods(['POST'])
def refresh(request):
    data = body(request) or {}
    token = str(data.get('refresh_token') or '')
    session = Session.objects.select_related('account').filter(refresh_token=token, revoked=False).first()
    now = timezone.now()
    if session is None or session.refresh_expires <= now or session.account.status != 'active':
        return err('登录已失效', 401)
    session.access_token = secrets.token_hex(24)
    session.access_expires = now + timedelta(minutes=setting_int('session_minutes', 120))
    session.save(update_fields=['access_token', 'access_expires'])
    return ok(token=session.access_token, refresh_token=session.refresh_token)


@require_http_methods(['POST'])
@login_required
def logout(request):
    request.session_row.revoked = True
    request.session_row.save(update_fields=['revoked'])
    log_op(request, 'logout', 'session', request.session_row.id)
    return ok()


@require_http_methods(['POST'])
def register(request):
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    username = str(data.get('username') or '').strip()
    password = str(data.get('password') or '')
    if len(username) < 3 or len(password) < setting_int('password_min', 6):
        return err('用户名至少 3 位，密码需满足强度要求')
    if Account.objects.filter(username=username).exists():
        return err('用户名已存在')
    Account.objects.create(
        username=username,
        password=hash_password(password),
        display_name=str(data.get('display_name') or username).strip(),
        email=str(data.get('email') or '').strip(),
        status='disabled',
        must_change_password=True,
    )
    return ok(message='已提交，等待管理员启用')


@require_http_methods(['GET'])
@login_required
def me(request):
    return ok(user=request.account.public(), permissions=_permissions(request.account), menus=_menu_tree(request.account))


@require_http_methods(['POST'])
@login_required
def profile(request):
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    account = request.account
    display_name = str(data.get('display_name') or '').strip()
    if not display_name:
        return err('请填写显示名称')
    account.display_name = display_name[:64]
    account.email = str(data.get('email') or '')[:128]
    account.phone = str(data.get('phone') or '')[:32]
    if data.get('avatar'):
        account.avatar = str(data.get('avatar'))[:255]
    account.save(update_fields=['display_name', 'email', 'phone', 'avatar'])
    log_op(request, 'update', 'profile', account.username)
    return ok(user=account.public())


@require_http_methods(['POST'])
@login_required
@idempotent
def password(request):
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    old_password = str(data.get('old_password') or '')
    new_password = str(data.get('new_password') or '')
    if not verify_password(old_password, request.account.password):
        return err('当前密码不正确')
    if len(new_password) < setting_int('password_min', 6):
        return err('新密码长度不足')
    request.account.password = hash_password(new_password)
    request.account.must_change_password = False
    request.account.save(update_fields=['password', 'must_change_password'])
    Session.objects.filter(account=request.account, revoked=False).exclude(id=request.session_row.id).update(revoked=True)
    request.session_row.access_token = secrets.token_hex(24)
    request.session_row.access_expires = timezone.now() + timedelta(minutes=setting_int('session_minutes', 120))
    request.session_row.save(update_fields=['access_token', 'access_expires'])
    log_op(request, 'update', 'password', request.account.username)
    return ok(token=request.session_row.access_token, user=request.account.public())


@require_http_methods(['GET', 'POST'])
@login_required
def preferences(request):
    if request.method == 'GET':
        try:
            data = json.loads(request.account.preferences or '{}')
        except json.JSONDecodeError:
            data = {}
        return ok(preferences=data)
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    request.account.preferences = json.dumps(data, ensure_ascii=False)
    request.account.save(update_fields=['preferences'])
    return ok()


def _recycle(request, model_name, obj, title):
    obj.is_deleted = True
    obj.save(update_fields=['is_deleted'])
    RecycleItem.objects.create(model_name=model_name, object_id=obj.id, title=title[:120], deleted_by=request.account)


@require_http_methods(['GET'])
@login_required
def users(request):
    qs = search(Account.objects.filter(is_deleted=False).select_related('dept', 'post'), request.GET.get('keyword'), ['username', 'display_name', 'phone'])
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET.get('status'))
    total, rows = paginate(request, qs.order_by('-id'))
    items = []
    for row in rows:
        item = row.public()
        item['phone'] = _mask_phone(item['phone'])
        items.append(item)
    return ok(items=items, total=total)


@require_http_methods(['POST'])
@login_required
@idempotent
def user_save(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    username = str(data.get('username') or '').strip()
    if not username:
        return err('请填写用户名')
    account = Account.objects.filter(id=data.get('id'), is_deleted=False).first() if data.get('id') else None
    if account is None:
        if Account.objects.filter(username=username).exists():
            return err('用户名已存在')
        password = str(data.get('password') or 'Local#8k2p')
        if len(password) < setting_int('password_min', 6):
            return err('密码长度不足')
        account = Account(username=username, password=hash_password(password))
    account.display_name = str(data.get('display_name') or username)[:64]
    account.email = str(data.get('email') or '')[:128]
    account.phone = str(data.get('phone') or '')[:32]
    account.dept_id = data.get('dept_id') or None
    account.post_id = data.get('post_id') or None
    account.status = data.get('status') if data.get('status') in ('active', 'disabled') else account.status or 'active'
    account.save()
    if isinstance(data.get('role_ids'), list):
        account.roles.set(Role.objects.filter(id__in=data.get('role_ids'), is_deleted=False))
    log_op(request, 'save', 'user', account.username)
    return ok(item=account.public())


@require_http_methods(['POST'])
@login_required
def user_delete(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    ids = data.get('ids') or []
    for account in Account.objects.filter(id__in=ids, is_deleted=False, is_super=False):
        _recycle(request, 'account', account, account.username)
    log_op(request, 'delete', 'user', ids)
    return ok()


@require_http_methods(['POST'])
@login_required
def user_status(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    status = data.get('status')
    if status not in ('active', 'disabled'):
        return err('状态不正确')
    Account.objects.filter(id__in=data.get('ids') or [], is_super=False).update(status=status)
    if status == 'disabled':
        Session.objects.filter(account_id__in=data.get('ids') or []).update(revoked=True)
    log_op(request, 'status', 'user', status)
    return ok()


@require_http_methods(['GET'])
@login_required
def roles(request):
    qs = search(Role.objects.filter(is_deleted=False), request.GET.get('keyword'), ['name', 'code'])
    total, rows = paginate(request, qs)
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['POST'])
@login_required
def role_save(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    name = str(data.get('name') or '').strip()
    code = str(data.get('code') or '').strip()
    if not name or not code:
        return err('请填写角色名称和编码')
    role = Role.objects.filter(id=data.get('id'), is_deleted=False).first() if data.get('id') else Role()
    if Role.objects.exclude(id=getattr(role, 'id', None)).filter(code=code).exists():
        return err('编码已存在')
    role.name = name
    role.code = code
    role.data_scope = data.get('data_scope') if data.get('data_scope') in ('self', 'dept', 'all') else 'self'
    role.remark = str(data.get('remark') or '')[:200]
    role.save()
    if isinstance(data.get('menu_ids'), list):
        role.menus.set(Menu.objects.filter(id__in=data.get('menu_ids')))
    log_op(request, 'save', 'role', role.code)
    return ok(item=role.public())


@require_http_methods(['POST'])
@login_required
def role_delete(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    for role in Role.objects.filter(id__in=data.get('ids') or [], is_deleted=False).exclude(code='super'):
        _recycle(request, 'role', role, role.name)
    return ok()


def _simple_list(request, model, fields):
    qs = model.objects.filter(is_deleted=False) if hasattr(model, 'is_deleted') else model.objects.all()
    qs = search(qs, request.GET.get('keyword'), fields)
    total, rows = paginate(request, qs)
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['GET'])
@login_required
def depts(request):
    rows = Department.objects.filter(is_deleted=False)
    return ok(items=[row.public() for row in rows], total=rows.count())


@require_http_methods(['POST'])
@login_required
def dept_save(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request)
    if data is None or not str(data.get('name') or '').strip():
        return err('请填写部门名称')
    dept = Department.objects.filter(id=data.get('id'), is_deleted=False).first() if data.get('id') else Department()
    dept.name = str(data.get('name')).strip()[:64]
    dept.parent_id = data.get('parent_id') or None
    dept.leader_name = str(data.get('leader_name') or '')[:64]
    dept.sort = int(data.get('sort') or 0)
    dept.save()
    log_op(request, 'save', 'dept', dept.name)
    return ok(item=dept.public())


@require_http_methods(['POST'])
@login_required
def dept_delete(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    for dept in Department.objects.filter(id__in=data.get('ids') or [], is_deleted=False):
        if dept.children.filter(is_deleted=False).exists() or dept.account_set.filter(is_deleted=False).exists():
            return err(f'{dept.name} 下还有下级或人员')
        _recycle(request, 'dept', dept, dept.name)
    return ok()


@require_http_methods(['GET'])
@login_required
def posts(request):
    return _simple_list(request, Post, ['name', 'code'])


@require_http_methods(['POST'])
@login_required
def post_save(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    post = Post.objects.filter(id=data.get('id'), is_deleted=False).first() if data.get('id') else Post()
    post.name = str(data.get('name') or '').strip()[:64]
    post.code = str(data.get('code') or '').strip()[:64]
    post.is_active = bool(data.get('is_active', True))
    if not post.name or not post.code:
        return err('请填写岗位名称和编码')
    post.save()
    return ok(item=post.public())


@require_http_methods(['POST'])
@login_required
def post_delete(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    for post in Post.objects.filter(id__in=data.get('ids') or [], is_deleted=False):
        _recycle(request, 'post', post, post.name)
    return ok()


@require_http_methods(['GET'])
@login_required
def menus(request):
    rows = Menu.objects.all()
    return ok(items=[row.public() for row in rows], total=rows.count())


@require_http_methods(['POST'])
@login_required
def menu_save(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request)
    if data is None or not str(data.get('name') or '').strip():
        return err('请填写菜单名称')
    menu = Menu.objects.filter(id=data.get('id')).first() if data.get('id') else Menu()
    for field in ('name', 'name_en', 'path', 'icon', 'component', 'menu_type', 'permission'):
        if field in data:
            setattr(menu, field, str(data.get(field) or '')[:128])
    menu.parent_id = data.get('parent_id') or None
    menu.sort = int(data.get('sort') or 0)
    menu.visible = bool(data.get('visible', True))
    menu.keep_alive = bool(data.get('keep_alive', True))
    menu.is_external = bool(data.get('is_external', False))
    menu.save()
    log_op(request, 'save', 'menu', menu.name)
    return ok(item=menu.public())


@require_http_methods(['POST'])
@login_required
def menu_delete(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    Menu.objects.filter(id__in=data.get('ids') or []).delete()
    return ok()


@require_http_methods(['GET'])
@login_required
def dicts(request):
    types = [row.public() for row in DictType.objects.filter(is_deleted=False)]
    items = [row.public() for row in DictItem.objects.filter(is_deleted=False, is_active=True).select_related('dict_type')]
    return ok(types=types, items=items)


@require_http_methods(['POST'])
@login_required
def dict_save(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    if data.get('kind') == 'item':
        item = DictItem.objects.filter(id=data.get('id')).first() if data.get('id') else DictItem(dict_type_id=data.get('dict_type_id'))
        item.label = str(data.get('label') or '')[:64]
        item.value = str(data.get('value') or '')[:64]
        item.sort = int(data.get('sort') or 0)
        item.is_active = bool(data.get('is_active', True))
        if not item.label:
            return err('请填写字典项')
        item.save()
        return ok(item=item.public())
    row = DictType.objects.filter(id=data.get('id'), is_deleted=False).first() if data.get('id') else DictType()
    row.name = str(data.get('name') or '')[:64]
    row.code = str(data.get('code') or '')[:64]
    row.is_active = bool(data.get('is_active', True))
    if not row.name or not row.code:
        return err('请填写字典名称和编码')
    row.save()
    return ok(item=row.public())


@require_http_methods(['POST'])
@login_required
def dict_delete(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    if data.get('kind') == 'item':
        DictItem.objects.filter(id__in=data.get('ids') or []).update(is_deleted=True)
    else:
        DictType.objects.filter(id__in=data.get('ids') or []).update(is_deleted=True)
    return ok()


@require_http_methods(['GET'])
@login_required
def serials(request):
    return ok(items=[row.public() for row in SerialRule.objects.all()])


@require_http_methods(['POST'])
@login_required
def serial_save(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    row = SerialRule.objects.filter(id=data.get('id')).first() if data.get('id') else SerialRule()
    row.name = str(data.get('name') or '')[:64]
    row.code = str(data.get('code') or '')[:64]
    row.prefix = str(data.get('prefix') or '')[:32]
    row.date_format = str(data.get('date_format') or '%Y%m%d')[:32]
    row.padding = int(data.get('padding') or 4)
    if not row.name or not row.code:
        return err('请填写规则名称和编码')
    row.save()
    return ok(item=row.public())


@require_http_methods(['POST'])
@login_required
def serial_next(request):
    data = body(request) or {}
    row = SerialRule.objects.filter(code=data.get('code')).first()
    if row is None:
        return err('规则不存在', 404)
    today = timezone.localtime().strftime(row.date_format or '%Y%m%d')
    number = f"{row.prefix}{today}{str(row.next_seq).zfill(row.padding)}"
    row.next_seq += 1
    row.save(update_fields=['next_seq'])
    return ok(number=number)


def _scope_notes(request, qs):
    if request.account.is_super:
        return qs
    scopes = set(request.account.roles.values_list('data_scope', flat=True))
    if 'all' in scopes:
        return qs
    if 'dept' in scopes and request.account.dept_id:
        return qs.filter(owner__dept_id=request.account.dept_id)
    return qs.filter(owner=request.account)


@require_http_methods(['GET'])
@login_required
def notes(request):
    qs = _scope_notes(request, Note.objects.filter(is_deleted=False).select_related('owner'))
    qs = search(qs, request.GET.get('keyword'), ['title', 'content'])
    ordering = request.GET.get('ordering') or '-updated_at'
    if ordering.lstrip('-') in ('title', 'updated_at', 'id'):
        qs = qs.order_by(ordering)
    total, rows = paginate(request, qs)
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['POST'])
@login_required
@idempotent
def note_save(request):
    data = body(request)
    if data is None or not str(data.get('title') or '').strip():
        return err('请填写标题')
    note = Note.objects.filter(id=data.get('id'), is_deleted=False).first() if data.get('id') else Note(owner=request.account)
    if note and note.id and not _scope_notes(request, Note.objects.filter(id=note.id)).exists():
        return err('没有权限', 403)
    note.title = str(data.get('title')).strip()[:120]
    note.content = str(data.get('content') or '')
    if not note.owner_id:
        note.owner = request.account
    note.save()
    log_op(request, 'save', 'note', note.title)
    return ok(item=note.public())


@require_http_methods(['POST'])
@login_required
def note_delete(request):
    data = body(request) or {}
    for note in _scope_notes(request, Note.objects.filter(id__in=data.get('ids') or [data.get('id')], is_deleted=False)):
        _recycle(request, 'note', note, note.title)
    return ok()


@require_http_methods(['GET'])
@login_required
def announcements(request):
    qs = search(Announcement.objects.filter(is_deleted=False), request.GET.get('keyword'), ['title'])
    total, rows = paginate(request, qs)
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['POST'])
@login_required
def announcement_save(request):
    data = body(request)
    if data is None or not str(data.get('title') or '').strip():
        return err('请填写标题')
    row = Announcement.objects.filter(id=data.get('id'), is_deleted=False).first() if data.get('id') else Announcement()
    row.title = str(data.get('title')).strip()[:120]
    row.content = str(data.get('content') or '')
    row.is_active = bool(data.get('is_active', True))
    row.save()
    return ok(item=row.public())


@require_http_methods(['POST'])
@login_required
def announcement_delete(request):
    data = body(request) or {}
    for row in Announcement.objects.filter(id__in=data.get('ids') or [], is_deleted=False):
        _recycle(request, 'announcement', row, row.title)
    return ok()


@require_http_methods(['GET'])
@login_required
def todos(request):
    qs = Todo.objects.filter(is_deleted=False, account=request.account)
    total, rows = paginate(request, qs)
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['POST'])
@login_required
def todo_save(request):
    data = body(request)
    if data is None or not str(data.get('title') or '').strip():
        return err('请填写事项')
    row = Todo.objects.filter(id=data.get('id'), account=request.account, is_deleted=False).first() if data.get('id') else Todo(account=request.account)
    row.title = str(data.get('title')).strip()[:120]
    row.due_date = str(data.get('due_date') or '')[:32]
    row.done = bool(data.get('done', False))
    row.save()
    return ok(item=row.public())


@require_http_methods(['POST'])
@login_required
def todo_delete(request):
    data = body(request) or {}
    for row in Todo.objects.filter(id__in=data.get('ids') or [], account=request.account, is_deleted=False):
        _recycle(request, 'todo', row, row.title)
    return ok()


@require_http_methods(['GET'])
@login_required
def approvals(request):
    qs = search(Approval.objects.filter(is_deleted=False).select_related('applicant'), request.GET.get('keyword'), ['title'])
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET.get('status'))
    total, rows = paginate(request, qs)
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['POST'])
@login_required
def approval_save(request):
    data = body(request)
    if data is None or not str(data.get('title') or '').strip():
        return err('请填写标题')
    row = Approval(applicant=request.account, status='pending')
    row.title = str(data.get('title')).strip()[:120]
    row.content = str(data.get('content') or '')
    row.save()
    Message.objects.create(account=request.account, title='审批已提交', content=row.title)
    return ok(item=row.public())


@require_http_methods(['POST'])
@login_required
def approval_act(request):
    data = body(request) or {}
    row = Approval.objects.filter(id=data.get('id'), is_deleted=False).first()
    if row is None:
        return err('审批不存在', 404)
    action = data.get('action')
    if action == 'withdraw' and row.applicant_id == request.account.id and row.status == 'pending':
        row.status = 'withdrawn'
    elif action in ('approve', 'reject') and row.status == 'pending':
        row.status = 'approved' if action == 'approve' else 'rejected'
        row.opinion = str(data.get('opinion') or '')[:255]
    else:
        return err('当前状态不能执行该操作')
    row.save(update_fields=['status', 'opinion', 'updated_at'])
    if row.applicant_id:
        Message.objects.create(account_id=row.applicant_id, title='审批有新进展', content=f'{row.title}：{row.status}')
    log_op(request, action, 'approval', row.title)
    return ok(item=row.public())


@require_http_methods(['GET'])
@login_required
def messages(request):
    qs = Message.objects.filter(account=request.account)
    total, rows = paginate(request, qs)
    unread = Message.objects.filter(account=request.account, is_read=False).count()
    return ok(items=[row.public() for row in rows], total=total, unread=unread)


@require_http_methods(['POST'])
@login_required
def message_read(request):
    data = body(request) or {}
    qs = Message.objects.filter(account=request.account)
    if data.get('ids'):
        qs = qs.filter(id__in=data.get('ids'))
    qs.update(is_read=True)
    return ok()


@require_http_methods(['GET'])
@login_required
def files(request):
    qs = StoredFile.objects.filter(is_deleted=False).select_related('uploader')
    total, rows = paginate(request, qs.order_by('-id'))
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['POST'])
@login_required
def file_upload(request):
    upload = request.FILES.get('file')
    if upload is None:
        return err('请选择文件')
    if upload.size > 20 * 1024 * 1024:
        return err('文件不能超过 20MB')
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored = f'{secrets.token_hex(8)}_{upload.name}'
    target = UPLOAD_DIR / stored
    with target.open('wb') as handle:
        for chunk in upload.chunks():
            handle.write(chunk)
    row = StoredFile.objects.create(
        name=upload.name,
        stored_name=stored,
        size=upload.size,
        content_type=upload.content_type or '',
        uploader=request.account,
    )
    return ok(item=row.public())


@require_http_methods(['POST'])
@login_required
def file_rename(request):
    data = body(request) or {}
    row = StoredFile.objects.filter(id=data.get('id'), is_deleted=False).first()
    if row is None:
        return err('文件不存在', 404)
    row.name = str(data.get('name') or row.name)[:255]
    row.save(update_fields=['name'])
    return ok(item=row.public())


@require_http_methods(['POST'])
@login_required
def file_delete(request):
    data = body(request) or {}
    for row in StoredFile.objects.filter(id__in=data.get('ids') or [], is_deleted=False):
        _recycle(request, 'file', row, row.name)
    return ok()


@require_http_methods(['GET'])
def file_raw(request, file_id):
    from core.api.common import current_session
    session = current_session(request)
    if session is None:
        return err('未登录或登录已失效', 401)
    row = StoredFile.objects.filter(id=file_id, is_deleted=False).first()
    if row is None:
        return err('文件不存在', 404)
    path = UPLOAD_DIR / row.stored_name
    if not path.is_file():
        return err('文件不存在', 404)
    return FileResponse(path.open('rb'), filename=row.name)


@require_http_methods(['GET'])
@login_required
def jobs(request):
    return ok(items=[row.public() for row in Job.objects.all()])


@require_http_methods(['POST'])
@login_required
def job_save(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request)
    if data is None:
        return err('请求格式不正确')
    row = Job.objects.filter(id=data.get('id')).first() if data.get('id') else Job(handler='ping')
    row.name = str(data.get('name') or row.name or '任务')[:64]
    row.cron = str(data.get('cron') or '* * * * *')[:64]
    row.handler = str(data.get('handler') or row.handler or 'ping')[:64]
    row.enabled = bool(data.get('enabled', True))
    row.save()
    return ok(item=row.public())


@require_http_methods(['POST'])
@login_required
def job_run(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    row = Job.objects.filter(id=data.get('id')).first()
    if row is None:
        return err('任务不存在', 404)
    execute(row)
    return ok(item=row.public())


@require_http_methods(['GET'])
@login_required
def login_logs(request):
    qs = search(LoginLog.objects.all(), request.GET.get('keyword'), ['username', 'ip', 'message'])
    total, rows = paginate(request, qs)
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['GET'])
@login_required
def operation_logs(request):
    qs = search(OperationLog.objects.select_related('account'), request.GET.get('keyword'), ['action', 'target', 'detail'])
    total, rows = paginate(request, qs)
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['GET'])
@login_required
def api_logs(request):
    qs = search(ApiLog.objects.all(), request.GET.get('keyword'), ['path', 'trace_id', 'ip'])
    total, rows = paginate(request, qs)
    return ok(items=[row.public() for row in rows], total=total)


@require_http_methods(['GET'])
@login_required
def logs_export(request):
    kind = request.GET.get('kind') or 'login'
    source = {'login': LoginLog, 'operation': OperationLog, 'api': ApiLog}[kind]
    rows = source.objects.all()[:1000]
    lines = [f'# exported by {request.account.username} at {timezone.localtime().strftime("%Y-%m-%d %H:%M")}']
    for row in rows:
        item = row.public()
        lines.append(','.join(str(item.get(key, '')).replace(',', ' ') for key in item))
    response = HttpResponse('\ufeff' + '\n'.join(lines), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{kind}-logs.csv"'
    return response


@require_http_methods(['GET'])
@login_required
def online_users(request):
    now = timezone.now()
    rows = Session.objects.filter(revoked=False, refresh_expires__gt=now).select_related('account')
    return ok(items=[row.public() for row in rows])


@require_http_methods(['POST'])
@login_required
def online_kick(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    Session.objects.filter(id__in=data.get('ids') or []).update(revoked=True)
    log_op(request, 'kick', 'session', data.get('ids'))
    return ok()


@require_http_methods(['GET'])
@login_required
def settings_get(request):
    return ok(
        items=[row.public() for row in Setting.objects.all()],
        flags=[row.public() for row in FeatureFlag.objects.all()],
    )


@require_http_methods(['POST'])
@login_required
def settings_save(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    for key, value in (data.get('settings') or {}).items():
        Setting.objects.update_or_create(key=str(key)[:64], defaults={'value': str(value)})
    for flag in data.get('flags') or []:
        FeatureFlag.objects.filter(id=flag.get('id')).update(enabled=bool(flag.get('enabled')))
    log_op(request, 'save', 'settings', '')
    return ok()


@require_http_methods(['GET'])
@login_required
def favorites(request):
    rows = Favorite.objects.filter(account=request.account).select_related('menu')
    return ok(items=[row.menu.public() for row in rows])


@require_http_methods(['POST'])
@login_required
def favorite_toggle(request):
    data = body(request) or {}
    menu = Menu.objects.filter(id=data.get('menu_id')).first()
    if menu is None:
        return err('菜单不存在', 404)
    row = Favorite.objects.filter(account=request.account, menu=menu).first()
    if row:
        row.delete()
        return ok(favorited=False)
    Favorite.objects.create(account=request.account, menu=menu)
    return ok(favorited=True)


@require_http_methods(['GET'])
@login_required
def recycle(request):
    total, rows = paginate(request, RecycleItem.objects.select_related('deleted_by'))
    return ok(items=[row.public() for row in rows], total=total)


_RESTORE = {
    'account': Account,
    'role': Role,
    'dept': Department,
    'post': Post,
    'note': Note,
    'announcement': Announcement,
    'todo': Todo,
    'file': StoredFile,
}


@require_http_methods(['POST'])
@login_required
def recycle_restore(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    data = body(request) or {}
    row = RecycleItem.objects.filter(id=data.get('id')).first()
    if row is None:
        return err('记录不存在', 404)
    model = _RESTORE.get(row.model_name)
    if model is None:
        return err('该记录不能恢复')
    model.objects.filter(id=row.object_id).update(is_deleted=False)
    row.delete()
    log_op(request, 'restore', row.model_name, row.title)
    return ok()


@require_http_methods(['GET'])
@login_required
def dashboard(request):
    try:
        days = int(request.GET.get('days') or 7)
    except (TypeError, ValueError):
        days = 7
    if days <= 1:
        days = 1
    elif days >= 30:
        days = 30
    else:
        days = 7
    return ok(
        user=request.account.public(),
        users=Account.objects.filter(is_deleted=False, status='active').count(),
        notes=Note.objects.filter(is_deleted=False).count(),
        files=StoredFile.objects.filter(is_deleted=False).count(),
        pending=Approval.objects.filter(is_deleted=False, status='pending').count(),
        unread=Message.objects.filter(account=request.account, is_read=False).count(),
        login_trend=_login_trend(days),
        announcements=[row.public() for row in Announcement.objects.filter(is_deleted=False, is_active=True)[:5]],
    )


def _login_trend(days=7):
    today = timezone.localdate()
    points = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        count = LoginLog.objects.filter(success=True, created_at__date=day).count()
        points.append({'day': day.isoformat(), 'count': count})
    return points


@require_http_methods(['POST'])
@login_required
def backup(request):
    if not request.account.is_super:
        return err('没有权限', 403)
    import shutil
    source = Path(settings.BASE_DIR).parent / 'data' / 'app.sqlite3'
    folder = source.parent / 'backups'
    folder.mkdir(parents=True, exist_ok=True)
    name = timezone.localtime().strftime('app-%Y%m%d-%H%M%S.sqlite3')
    shutil.copy2(source, folder / name)
    log_op(request, 'backup', 'database', name)
    names = sorted(path.name for path in folder.glob('*.sqlite3'))
    return ok(file=name, files=names[-10:])
