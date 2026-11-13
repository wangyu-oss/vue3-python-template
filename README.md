# Vue 3 + Python 管理系统

Vue 3 管理台、Django 接口、SQLite 数据库。双击 `start.bat` 安装依赖并启动。

## 环境

- Python 3.10 或更高版本
- Node.js 18 或更高版本

## 启动

Windows 双击仓库根目录的 `start.bat`。停止双击 `stop.bat`。

| 说明 | 值 |
| --- | --- |
| 前端 | http://localhost:5173 |
| 后端 | http://localhost:8000 |
| 健康检查 | http://localhost:8000/api/v1/health |
| 管理员 | `admin` / `123456` |
| 普通用户 | `zhangsan` / `123456` |

登录页会预填管理员账号。

## 本机可用

- 登录会话：记住登录、访问令牌和刷新令牌、注销、登录失败锁定、会话超时
- 用户、角色、部门、岗位、菜单、按钮权限、数据范围
- 字典、编号、笔记、公告、待办、审批、文件、站内信
- 操作日志、登录日志、接口日志、在线用户、回收站、定时任务
- 亮色 / 暗色、布局、字号、中英文、页面水印
- 概览图表、系统设置、数据库备份

数据库文件是 `data/app.sqlite3`。上传文件保存在 `data/uploads`。

## 演示项

短信、邮件、第三方登录、对象存储、WebSocket、Celery、Redis 和支付等不连接外部服务。这些入口在「扩展能力」页，点击后只给出演示提示。

## 手动启动

```bat
cd python
python -m venv myenv
myenv\Scripts\python -m pip install -r requirements.txt
myenv\Scripts\python manage.py migrate
myenv\Scripts\python seed_demo.py
myenv\Scripts\python manage.py runserver 0.0.0.0:8000
```

另开一个终端：

```bat
cd web
npm install
npm run dev
```
