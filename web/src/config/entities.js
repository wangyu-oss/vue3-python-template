const statusOptions = [
  { label: '启用', value: 'active' },
  { label: '停用', value: 'disabled' },
]
const scopeOptions = [
  { label: '本人', value: 'self' },
  { label: '本部门', value: 'dept' },
  { label: '全部', value: 'all' },
]
const approvalOptions = [
  { label: '待处理', value: 'pending' },
  { label: '已同意', value: 'approved' },
  { label: '已驳回', value: 'rejected' },
  { label: '已撤回', value: 'withdrawn' },
]

export const entities = {
  '/users': {
    keyword: true,
    selection: true,
    batchStatus: true,
    createPermission: 'user:create',
    deletePermission: 'user:delete',
    columns: [
      { prop: 'username', label: '用户名' },
      { prop: 'display_name', label: '显示名称' },
      { prop: 'dept_name', label: '部门' },
      { prop: 'phone', label: '手机' },
      { prop: 'status', label: '状态' },
    ],
    fields: [
      { prop: 'username', label: '用户名', required: true },
      { prop: 'display_name', label: '显示名称', required: true },
      { prop: 'password', label: '初始密码', createOnly: true },
      { prop: 'email', label: '邮箱' },
      { prop: 'phone', label: '手机' },
      { prop: 'dept_id', label: '部门', type: 'select', source: '/depts' },
      { prop: 'post_id', label: '岗位', type: 'select', source: '/posts' },
      { prop: 'role_ids', label: '角色', type: 'select', source: '/roles', multiple: true },
      { prop: 'status', label: '状态', type: 'select', options: statusOptions },
    ],
  },
  '/roles': {
    keyword: true,
    selection: true,
    deletePermission: 'user:delete',
    columns: [
      { prop: 'name', label: '角色' },
      { prop: 'code', label: '编码' },
      { prop: 'data_scope', label: '数据范围' },
      { prop: 'remark', label: '说明' },
    ],
    fields: [
      { prop: 'name', label: '角色', required: true },
      { prop: 'code', label: '编码', required: true },
      { prop: 'data_scope', label: '数据范围', type: 'select', options: scopeOptions },
      { prop: 'remark', label: '说明' },
      { prop: 'menu_ids', label: '权限', type: 'menus' },
    ],
  },
  '/depts': {
    selection: true,
    columns: [
      { prop: 'name', label: '部门' },
      { prop: 'leader_name', label: '负责人' },
      { prop: 'parent_id', label: '上级编号' },
      { prop: 'sort', label: '排序' },
    ],
    fields: [
      { prop: 'name', label: '部门', required: true },
      { prop: 'leader_name', label: '负责人' },
      { prop: 'parent_id', label: '上级部门', type: 'select', source: '/depts' },
      { prop: 'sort', label: '排序', type: 'number' },
    ],
  },
  '/posts': {
    keyword: true,
    selection: true,
    columns: [
      { prop: 'name', label: '岗位' },
      { prop: 'code', label: '编码' },
      { prop: 'is_active', label: '启用' },
    ],
    fields: [
      { prop: 'name', label: '岗位', required: true },
      { prop: 'code', label: '编码', required: true },
      { prop: 'is_active', label: '启用', type: 'switch' },
    ],
  },
  '/menus': {
    selection: true,
    columns: [
      { prop: 'name', label: '名称' },
      { prop: 'path', label: '路径' },
      { prop: 'menu_type', label: '类型' },
      { prop: 'permission', label: '权限码' },
      { prop: 'sort', label: '排序' },
    ],
    fields: [
      { prop: 'name', label: '名称', required: true },
      { prop: 'name_en', label: '英文名' },
      { prop: 'path', label: '路径' },
      { prop: 'icon', label: '图标' },
      { prop: 'component', label: '组件' },
      { prop: 'menu_type', label: '类型', type: 'select', options: [
        { label: '目录', value: 'dir' },
        { label: '菜单', value: 'menu' },
        { label: '按钮', value: 'button' },
      ] },
      { prop: 'permission', label: '权限码' },
      { prop: 'parent_id', label: '上级', type: 'select', source: '/menus' },
      { prop: 'sort', label: '排序', type: 'number' },
      { prop: 'visible', label: '显示', type: 'switch' },
    ],
  },
  '/notes': {
    keyword: true,
    selection: true,
    sortable: true,
    createPermission: 'note:create',
    deletePermission: 'note:delete',
    columns: [
      { prop: 'title', label: '标题', sort: 'title' },
      { prop: 'content', label: '内容' },
      { prop: 'owner_name', label: '所属人' },
      { prop: 'updated_at', label: '更新时间', sort: 'updated_at' },
    ],
    fields: [
      { prop: 'title', label: '标题', required: true },
      { prop: 'content', label: '内容', type: 'textarea' },
    ],
  },
  '/announcements': {
    keyword: true,
    selection: true,
    columns: [
      { prop: 'title', label: '标题' },
      { prop: 'content', label: '内容' },
      { prop: 'is_active', label: '发布' },
    ],
    fields: [
      { prop: 'title', label: '标题', required: true },
      { prop: 'content', label: '内容', type: 'textarea' },
      { prop: 'is_active', label: '发布', type: 'switch' },
    ],
  },
  '/todos': {
    selection: true,
    columns: [
      { prop: 'title', label: '事项' },
      { prop: 'due_date', label: '日期' },
      { prop: 'done', label: '完成' },
    ],
    fields: [
      { prop: 'title', label: '事项', required: true },
      { prop: 'due_date', label: '日期' },
      { prop: 'done', label: '完成', type: 'switch' },
    ],
  },
  '/approvals': {
    keyword: true,
    columns: [
      { prop: 'title', label: '标题' },
      { prop: 'applicant_name', label: '申请人' },
      { prop: 'status', label: '状态' },
      { prop: 'opinion', label: '意见' },
    ],
    fields: [
      { prop: 'title', label: '标题', required: true },
      { prop: 'content', label: '内容', type: 'textarea' },
    ],
    actions: [
      { key: 'approve', label: '同意' },
      { key: 'reject', label: '驳回' },
      { key: 'withdraw', label: '撤回' },
    ],
  },
  '/serials': {
    columns: [
      { prop: 'name', label: '名称' },
      { prop: 'code', label: '编码' },
      { prop: 'prefix', label: '前缀' },
      { prop: 'next_seq', label: '下一序号' },
    ],
    fields: [
      { prop: 'name', label: '名称', required: true },
      { prop: 'code', label: '编码', required: true },
      { prop: 'prefix', label: '前缀' },
      { prop: 'date_format', label: '日期格式' },
      { prop: 'padding', label: '位数', type: 'number' },
    ],
    next: true,
  },
}

export { approvalOptions }
