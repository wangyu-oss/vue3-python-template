#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djWeb.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        venv_py = root / 'myenv' / 'Scripts' / 'python.exe'
        hint = ''
        if venv_py.is_file() and Path(sys.executable).resolve() != venv_py.resolve():
            hint = (
                f'\n当前解释器: {sys.executable}\n'
                f'请改用虚拟环境: {venv_py}\n'
                f'或双击运行仓库根目录 start.bat'
            )
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
            + hint
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
