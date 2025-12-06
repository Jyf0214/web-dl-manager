#!/usr/bin/env python3
"""
测试日志配置脚本
"""
import os
import sys
import logging

# 添加app目录到路径
sys.path.insert(0, '/root/web-dl-manager/app')

def test_logging():
    """测试日志配置"""
    print("测试日志配置...")
    
    # 设置DEBUG模式环境变量
    os.environ["DEBUG_MODE"] = "true"
    
    # 导入并测试日志
    from app.main import main_app
    from app.tasks import debug_enabled, logger
    
    print(f"DEBUG_MODE环境变量: {os.getenv('DEBUG_MODE')}")
    print(f"tasks.py中的debug_enabled: {debug_enabled}")
    
    # 测试日志输出
    logger.debug("这是一条DEBUG级别的测试日志")
    logger.info("这是一条INFO级别的测试日志")
    logger.warning("这是一条WARNING级别的测试日志")
    logger.error("这是一条ERROR级别的测试日志")
    
    print("日志配置测试完成")

if __name__ == "__main__":
    test_logging()