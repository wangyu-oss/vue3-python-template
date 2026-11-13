import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djWeb.settings')
django.setup()

from core.models import (
    Account,
    Announcement,
    Approval,
    Department,
    DictItem,
    DictType,
    FeatureFlag,
    Job,
    Menu,
    Message,
    Note,
    Post,
    Role,
    SerialRule,
    Setting,
    Todo,
)
from core.passwords import hash_password


MENUS = [
    ('概览', 'Home', '/home', 'House', 'home', '', 10),
    ('业务', 'Work', '', 'Folder', 'dir', '', 20),
    ('笔记', 'Notes', '/notes', 'EditPen', 'entity', 'note:view', 21),
    ('公告', 'Notices', '/announcements', 'Bell', 'entity', 'notice:view', 22),
    ('待办', 'Todos', '/todos', 'Finished', 'entity', 'todo:view', 23),
    ('审批', 'Approvals', '/approvals', 'Stamp', 'entity', 'approval:view', 24),
    ('文件', 'Files', '/files', 'FolderOpened', 'files', 'file:view', 25),
    ('消息', 'Messages', '/messages', 'ChatDotRound', 'messages', 'message:view', 26),
    ('组织权限', 'Access', '', 'Lock', 'dir', '', 30),
    ('用户', 'Users', '/users', 'User', 'entity', 'user:view', 31),
    ('角色', 'Roles', '/roles', 'Avatar', 'entity', 'role:view', 32),
    ('部门', 'Departments', '/depts', 'OfficeBuilding', 'entity', 'dept:view', 33),
    ('岗位', 'Posts', '/posts', 'Postcard', 'entity', 'post:view', 34),
    ('菜单', 'Menus', '/menus', 'Menu', 'entity', 'menu:view', 35),
    ('系统', 'System', '', 'Setting', 'dir', '', 40),
    ('字典', 'Dictionaries', '/dicts', 'Collection', 'dicts', 'dict:view', 41),
    ('编号规则', 'Serials', '/serials', 'Ticket', 'entity', 'serial:view', 42),
    ('定时任务', 'Jobs', '/jobs', 'Timer', 'jobs', 'job:view', 43),
    ('系统设置', 'Settings', '/settings', 'Tools', 'settings', 'setting:view', 44),
    ('审计', 'Audit', '', 'Document', 'dir', '', 50),
    ('登录日志', 'Login logs', '/logs/login', 'Key', 'logs', 'log:view', 51),
    ('操作日志', 'Operation logs', '/logs/operation', 'List', 'logs', 'log:view', 52),
    ('接口日志', 'API logs', '/logs/api', 'Connection', 'logs', 'log:view', 53),
    ('在线用户', 'Online', '/online', 'Monitor', 'online', 'online:view', 54),
    ('回收站', 'Recycle', '/recycle', 'Delete', 'recycle', 'recycle:view', 55),
    ('扩展能力', 'Extensions', '/demo', 'MagicStick', 'demo', '', 60),
]

BUTTONS = [
    ('新增用户', 'user:create'),
    ('编辑用户', 'user:update'),
    ('删除用户', 'user:delete'),
    ('新增笔记', 'note:create'),
    ('删除笔记', 'note:delete'),
    ('导出', 'log:export'),
    ('备份', 'backup:run'),
]


def _menu(name, name_en, path, icon, component, permission, sort, parent=None, menu_type='menu'):
    return Menu.objects.create(
        name=name,
        name_en=name_en,
        path=path,
        icon=icon,
        component=component,
        permission=permission,
        sort=sort,
        parent=parent,
        menu_type=menu_type,
        visible=menu_type != 'button',
    )


def main():
    if Menu.objects.exists():
        account, _ = Account.objects.get_or_create(
            username='admin',
            defaults={
                'password': hash_password('123456'),
                'display_name': '管理员',
                'is_super': True,
                'status': 'active',
            },
        )
        print(f'ready: {account.username}')
        return

    root = Department.objects.create(name='总部', leader_name='管理员', sort=1)
    team = Department.objects.create(name='研发部', parent=root, leader_name='张三', sort=1)
    post = Post.objects.create(name='系统管理员', code='admin')
    member_post = Post.objects.create(name='专员', code='staff')
    super_role = Role.objects.create(name='超级管理员', code='super', data_scope='all', remark='全部数据')
    staff_role = Role.objects.create(name='专员', code='staff', data_scope='self', remark='仅本人数据')

    parents = {}
    created = []
    for name, name_en, path, icon, component, permission, sort in MENUS:
        menu_type = 'dir' if component == 'dir' else 'menu'
        parent = None
        if sort % 10 != 0:
            parent = parents.get(sort // 10 * 10)
        menu = _menu(name, name_en, path, icon, component, permission, sort, parent, menu_type)
        if menu_type == 'dir':
            parents[sort] = menu
        created.append(menu)
    for name, permission in BUTTONS:
        created.append(_menu(name, permission, '', '', 'button', permission, 0, menu_type='button'))
    super_role.menus.set(created)
    staff_paths = {'/home', '/notes', '/todos', '/messages', '/announcements', '/approvals', '/files'}
    staff_role.menus.set([item for item in created if item.path in staff_paths or item.permission in ('note:create', 'note:delete')])

    admin = Account.objects.create(
        username='admin',
        password=hash_password('123456'),
        display_name='管理员',
        email='admin@localhost',
        phone='13800000000',
        dept=root,
        post=post,
        is_super=True,
        status='active',
    )
    admin.roles.add(super_role)
    staff = Account.objects.create(
        username='zhangsan',
        password=hash_password('123456'),
        display_name='张三',
        email='zhangsan@localhost',
        phone='13900000000',
        dept=team,
        post=member_post,
        status='active',
    )
    staff.roles.add(staff_role)

    status = DictType.objects.create(name='状态', code='status')
    DictItem.objects.create(dict_type=status, label='启用', value='active', sort=1)
    DictItem.objects.create(dict_type=status, label='停用', value='disabled', sort=2)
    approval = DictType.objects.create(name='审批状态', code='approval_status')
    for index, (label, value) in enumerate([('待处理', 'pending'), ('已同意', 'approved'), ('已驳回', 'rejected'), ('已撤回', 'withdrawn')]):
        DictItem.objects.create(dict_type=approval, label=label, value=value, sort=index)
    SerialRule.objects.create(name='通用编号', code='common', prefix='NO', date_format='%Y%m%d', padding=4)
    Note.objects.create(
        title='采购合同评审',
        content='核对付款节点、验收标准与违约条款，评审意见提交法务归档。',
        owner=admin,
    )
    Note.objects.create(
        title='季度预算执行',
        content='研发费用已执行 68%，差旅与外包支出需在 11 月 20 日前完成复核。',
        owner=staff,
    )
    Announcement.objects.create(
        title='11 月权限复核',
        content='请各部门负责人于 11 月 18 日前完成账号与角色核对，异常权限提交信息安全组。',
    )
    Message.objects.create(
        account=admin,
        title='审批待处理',
        content='您有 1 条账号开通申请待审批，请在今日 18:00 前处理。',
    )
    Todo.objects.create(account=admin, title='完成角色权限复核', due_date='2026-11-20')
    Approval.objects.create(
        title='账号开通申请',
        content='申请为财务部新增结算专员账号，权限范围为本部门单据查询与提交。',
        applicant=staff,
        status='pending',
    )
    Job.objects.create(name='清理接口日志', cron='0 3 * * *', handler='cleanup_logs', enabled=True)
    Job.objects.create(name='巡检', cron='0 * * * *', handler='ping', enabled=False)
    for key, value in {
        'site_name': '管理系统',
        'copyright': '本地管理系统',
        'contact': 'admin@localhost',
        'password_min': '6',
        'login_fail_limit': '5',
        'lock_minutes': '15',
        'session_minutes': '120',
        'allow_multi_login': 'yes',
        'watermark': 'no',
        'ip_mode': 'off',
        'ip_list': '',
        'primary_color': '#0f766e',
    }.items():
        Setting.objects.create(key=key, value=value)
    FeatureFlag.objects.create(key='dashboard_chart', name='概览图表', enabled=True)
    FeatureFlag.objects.create(key='watermark', name='页面水印', enabled=False)
    print('ready: admin')


if __name__ == '__main__':
    main()
