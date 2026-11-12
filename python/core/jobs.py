import threading
import time

from django.utils import timezone

from core.models import ApiLog, Job

_STARTED = False


def field_match(expr, value):
    if expr == '*':
        return True
    if expr.startswith('*/'):
        step = int(expr[2:] or '1')
        return step > 0 and value % step == 0
    return int(expr) == value


def cron_match(expr, now):
    parts = (expr or '').split()
    if len(parts) != 5:
        return False
    weekday = (now.weekday() + 1) % 7
    values = [now.minute, now.hour, now.day, now.month, weekday]
    try:
        return all(field_match(part, value) for part, value in zip(parts, values))
    except ValueError:
        return False


def run_handler(job):
    if job.handler == 'cleanup_logs':
        cutoff = timezone.now() - timezone.timedelta(days=7)
        deleted, _ = ApiLog.objects.filter(created_at__lt=cutoff).delete()
        return f'清理接口日志 {deleted} 条'
    if job.handler == 'ping':
        return '执行完成'
    return '未知任务'


def execute(job):
    try:
        message = run_handler(job)
        job.last_status = 'success'
        job.last_message = message
    except Exception as exc:
        job.last_status = 'failed'
        job.last_message = str(exc)[:200]
    job.last_run = timezone.now()
    job.save(update_fields=['last_status', 'last_message', 'last_run'])
    return job


def _loop():
    seen = {}
    while True:
        time.sleep(60)
        now = timezone.localtime()
        stamp = now.strftime('%Y%m%d%H%M')
        try:
            for job in Job.objects.filter(enabled=True):
                if not cron_match(job.cron, now):
                    continue
                key = f'{job.id}:{stamp}'
                if seen.get(key):
                    continue
                seen[key] = True
                execute(job)
        except Exception:
            continue
        if len(seen) > 500:
            seen.clear()


def start():
    global _STARTED
    if _STARTED:
        return
    _STARTED = True
    threading.Thread(target=_loop, daemon=True).start()
