from django.db import models
from django.utils import timezone


def fmt_dt(value):
    if not value:
        return ''
    if getattr(value, 'tzinfo', None) is not None:
        value = timezone.localtime(value)
    if hasattr(value, 'hour'):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value.strftime('%Y-%m-%d')


class Department(models.Model):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    leader_name = models.CharField(max_length=64, blank=True, default='')
    sort = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['sort', 'id']

    def public(self):
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'leader_name': self.leader_name,
            'sort': self.sort,
        }


class Post(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def public(self):
        return {'id': self.id, 'name': self.name, 'code': self.code, 'is_active': self.is_active}


class Role(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)
    data_scope = models.CharField(max_length=16, default='all')
    remark = models.CharField(max_length=200, blank=True, default='')
    menus = models.ManyToManyField('Menu', blank=True, related_name='roles')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def public(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'data_scope': self.data_scope,
            'remark': self.remark,
            'menu_ids': list(self.menus.values_list('id', flat=True)),
        }


class Menu(models.Model):
    name = models.CharField(max_length=64)
    name_en = models.CharField(max_length=64, blank=True, default='')
    path = models.CharField(max_length=128, blank=True, default='')
    icon = models.CharField(max_length=64, blank=True, default='Menu')
    component = models.CharField(max_length=64, blank=True, default='')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    sort = models.IntegerField(default=0)
    menu_type = models.CharField(max_length=16, default='menu')
    permission = models.CharField(max_length=64, blank=True, default='')
    visible = models.BooleanField(default=True)
    keep_alive = models.BooleanField(default=True)
    is_external = models.BooleanField(default=False)

    class Meta:
        ordering = ['sort', 'id']

    def public(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en or self.name,
            'path': self.path,
            'icon': self.icon,
            'component': self.component,
            'parent_id': self.parent_id,
            'sort': self.sort,
            'menu_type': self.menu_type,
            'permission': self.permission,
            'visible': self.visible,
            'keep_alive': self.keep_alive,
            'is_external': self.is_external,
        }


class Account(models.Model):
    username = models.CharField(max_length=64, unique=True)
    password = models.CharField(max_length=255)
    display_name = models.CharField(max_length=64, blank=True, default='')
    email = models.CharField(max_length=128, blank=True, default='')
    phone = models.CharField(max_length=32, blank=True, default='')
    avatar = models.CharField(max_length=255, blank=True, default='')
    token = models.CharField(max_length=64, blank=True, default='')
    dept = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.SET_NULL)
    roles = models.ManyToManyField(Role, blank=True, related_name='accounts')
    status = models.CharField(max_length=16, default='active')
    must_change_password = models.BooleanField(default=False)
    failed_logins = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    is_super = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    preferences = models.TextField(blank=True, default='{}')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def public(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name or self.username,
            'email': self.email,
            'phone': self.phone,
            'avatar': self.avatar,
            'dept_id': self.dept_id,
            'dept_name': self.dept.name if self.dept_id else '',
            'post_id': self.post_id,
            'post_name': self.post.name if self.post_id else '',
            'status': self.status,
            'must_change_password': self.must_change_password,
            'is_super': self.is_super,
            'role_ids': list(self.roles.values_list('id', flat=True)),
            'created_at': self.created_at and fmt_dt(self.created_at) or '',
        }


class Session(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sessions')
    access_token = models.CharField(max_length=64, unique=True)
    refresh_token = models.CharField(max_length=64, unique=True)
    ip = models.CharField(max_length=64, blank=True, default='')
    user_agent = models.CharField(max_length=255, blank=True, default='')
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    access_expires = models.DateTimeField()
    refresh_expires = models.DateTimeField()

    def public(self):
        return {
            'id': self.id,
            'username': self.account.username,
            'display_name': self.account.display_name or self.account.username,
            'ip': self.ip,
            'user_agent': self.user_agent,
            'created_at': fmt_dt(self.created_at),
        }


class Note(models.Model):
    title = models.CharField(max_length=120)
    content = models.TextField(blank=True, default='')
    owner = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']

    def public(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'owner_id': self.owner_id,
            'owner_name': self.owner.display_name if self.owner_id else '',
            'created_at': fmt_dt(self.created_at),
            'updated_at': fmt_dt(self.updated_at),
        }


class DictType(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def public(self):
        return {'id': self.id, 'name': self.name, 'code': self.code, 'is_active': self.is_active}


class DictItem(models.Model):
    dict_type = models.ForeignKey(DictType, on_delete=models.CASCADE, related_name='items')
    label = models.CharField(max_length=64)
    value = models.CharField(max_length=64)
    sort = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['sort', 'id']

    def public(self):
        return {
            'id': self.id,
            'dict_type_id': self.dict_type_id,
            'dict_code': self.dict_type.code,
            'label': self.label,
            'value': self.value,
            'sort': self.sort,
            'is_active': self.is_active,
        }


class SerialRule(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)
    prefix = models.CharField(max_length=32, blank=True, default='')
    date_format = models.CharField(max_length=32, blank=True, default='%Y%m%d')
    next_seq = models.IntegerField(default=1)
    padding = models.IntegerField(default=4)

    def public(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'prefix': self.prefix,
            'date_format': self.date_format,
            'next_seq': self.next_seq,
            'padding': self.padding,
        }


class StoredFile(models.Model):
    name = models.CharField(max_length=255)
    stored_name = models.CharField(max_length=255)
    size = models.IntegerField(default=0)
    content_type = models.CharField(max_length=128, blank=True, default='')
    uploader = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def public(self):
        return {
            'id': self.id,
            'name': self.name,
            'size': self.size,
            'content_type': self.content_type,
            'uploader_name': self.uploader.display_name if self.uploader_id else '',
            'created_at': fmt_dt(self.created_at),
        }


class Message(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='messages')
    title = models.CharField(max_length=120)
    content = models.TextField(blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': fmt_dt(self.created_at),
        }


class Approval(models.Model):
    title = models.CharField(max_length=120)
    content = models.TextField(blank=True, default='')
    applicant = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name='approvals')
    status = models.CharField(max_length=16, default='pending')
    opinion = models.CharField(max_length=255, blank=True, default='')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'applicant_name': self.applicant.display_name if self.applicant_id else '',
            'applicant_id': self.applicant_id,
            'status': self.status,
            'opinion': self.opinion,
            'created_at': fmt_dt(self.created_at),
        }


class Announcement(models.Model):
    title = models.CharField(max_length=120)
    content = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'is_active': self.is_active,
            'created_at': fmt_dt(self.created_at),
        }


class Todo(models.Model):
    account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    due_date = models.CharField(max_length=32, blank=True, default='')
    done = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['done', '-id']

    def public(self):
        return {
            'id': self.id,
            'title': self.title,
            'due_date': self.due_date,
            'done': self.done,
            'created_at': fmt_dt(self.created_at),
        }


class Job(models.Model):
    name = models.CharField(max_length=64)
    cron = models.CharField(max_length=64, default='0 * * * *')
    handler = models.CharField(max_length=64)
    enabled = models.BooleanField(default=True)
    last_status = models.CharField(max_length=16, blank=True, default='')
    last_message = models.CharField(max_length=255, blank=True, default='')
    last_run = models.DateTimeField(null=True, blank=True)

    def public(self):
        return {
            'id': self.id,
            'name': self.name,
            'cron': self.cron,
            'handler': self.handler,
            'enabled': self.enabled,
            'last_status': self.last_status,
            'last_message': self.last_message,
            'last_run': fmt_dt(self.last_run),
        }


class LoginLog(models.Model):
    username = models.CharField(max_length=64, blank=True, default='')
    ip = models.CharField(max_length=64, blank=True, default='')
    user_agent = models.CharField(max_length=255, blank=True, default='')
    success = models.BooleanField(default=False)
    message = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'username': self.username,
            'ip': self.ip,
            'user_agent': self.user_agent,
            'success': self.success,
            'message': self.message,
            'created_at': fmt_dt(self.created_at),
        }


class OperationLog(models.Model):
    account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64)
    target = models.CharField(max_length=64, blank=True, default='')
    detail = models.TextField(blank=True, default='')
    ip = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'username': self.account.username if self.account_id else '',
            'action': self.action,
            'target': self.target,
            'detail': self.detail,
            'ip': self.ip,
            'created_at': fmt_dt(self.created_at),
        }


class ApiLog(models.Model):
    trace_id = models.CharField(max_length=32, blank=True, default='')
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=255)
    status_code = models.IntegerField(default=0)
    duration_ms = models.IntegerField(default=0)
    ip = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'trace_id': self.trace_id,
            'method': self.method,
            'path': self.path,
            'status_code': self.status_code,
            'duration_ms': self.duration_ms,
            'ip': self.ip,
            'created_at': fmt_dt(self.created_at),
        }


class Setting(models.Model):
    key = models.CharField(max_length=64, unique=True)
    value = models.TextField(blank=True, default='')

    def public(self):
        return {'key': self.key, 'value': self.value}


class FeatureFlag(models.Model):
    key = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=64)
    enabled = models.BooleanField(default=False)

    def public(self):
        return {'id': self.id, 'key': self.key, 'name': self.name, 'enabled': self.enabled}


class Favorite(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='favorites')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('account', 'menu')


class RecycleItem(models.Model):
    model_name = models.CharField(max_length=64)
    object_id = models.IntegerField()
    title = models.CharField(max_length=120, blank=True, default='')
    deleted_by = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'model_name': self.model_name,
            'object_id': self.object_id,
            'title': self.title,
            'deleted_by': self.deleted_by.username if self.deleted_by_id else '',
            'created_at': fmt_dt(self.created_at),
        }
