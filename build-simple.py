#!/usr/bin/env python3
"""
简化的 PyInstaller 构建脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def build_with_pyinstaller():
    """使用 PyInstaller 构建"""
    
    # 确保在项目根目录
    os.chdir(Path(__file__).parent)
    
    # 构建命令
    cmd = [
        'pyinstaller',
        '--name=web-dl-manager',
        '--onefile',
        '--clean',
        '--noconfirm',
        '--add-data=app/templates:app/templates',
        '--add-data=app/requirements.txt:app',
        '--add-data=entrypoint.sh:.',
        '--hidden-import=app.config',
        '--hidden-import=app.database',
        '--hidden-import=app.logging_handler',
        '--hidden-import=app.main',
        '--hidden-import=app.mega_upload',
        '--hidden-import=app.openlist',
        '--hidden-import=app.status',
        '--hidden-import=app.tasks',
        '--hidden-import=app.updater',
        '--hidden-import=app.utils',
        '--hidden-import=jinja2',
        '--hidden-import=jinja2.ext',
        '--hidden-import=passlib.handlers.bcrypt',
        '--hidden-import=mysql.connector',
        '--hidden-import=gofilepy_api',
        '--hidden-import=mega',
        '--hidden-import=aiofiles',
        '--hidden-import=itsdangerous',
        '--hidden-import=python_jose',
        '--hidden-import=starlette.middleware.sessions',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.logging',
        'app/main.py'
    ]
    
    print("开始构建二进制文件...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建输出:")
        print(result.stdout)
        if result.stderr:
            print("构建警告/错误:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("错误: PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        sys.exit(1)
    
    print("\n构建完成！")
    
    # 检查结果
    dist_dir = Path('dist')
    if dist_dir.exists():
        binary_path = dist_dir / 'web-dl-manager'
        if binary_path.exists():
            print(f"二进制文件已创建: {binary_path.absolute()}")
            # 显示文件大小
            size_mb = binary_path.stat().st_size / (1024 * 1024)
            print(f"文件大小: {size_mb:.2f} MB")
        else:
            print("警告: 未找到二进制文件")

if __name__ == "__main__":
    build_with_pyinstaller()