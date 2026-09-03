"""
日志系统模块
配置全局 logging，支持文件输出和控制台输出
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_dir: str, level: str = "INFO", console: bool = False) -> None:
    """
    初始化全局日志系统
    
    Args:
        log_dir: 日志文件存放目录
        level: 日志级别 DEBUG/INFO/WARNING/ERROR
        console: 是否同时输出到控制台（调试用）
    """
    log_path = Path(os.path.expanduser(log_dir))
    log_path.mkdir(parents=True, exist_ok=True)

    app_log = log_path / "app.log"

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 清除已有处理器（避免重复）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 文件处理器（按大小轮转，单文件 5MB，保留 3 个备份）
    file_handler = RotatingFileHandler(
        app_log, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 控制台处理器（可选，调试用）
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    logging.info(f"[Logger] 日志系统初始化完成，输出目录: {log_path}")
