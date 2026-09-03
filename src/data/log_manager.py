"""
操作日志管理模块
按自然日分文件记录按钮点击、紧急事件等用户操作
独立于系统日志（app.log），便于家属查看和统计
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import threading


class OperationLogManager:
    """
    操作日志管理器（线程安全）
    
    日志格式: YYYY-MM-DD HH:MM:SS | event_type | details
    文件命名: YYYY-MM-DD.txt
    """
    def __init__(self, log_dir: str):
        self.log_dir = Path(os.path.expanduser(log_dir))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._current_date: Optional[str] = None
        self._current_file: Optional[Path] = None

    def _get_file_path(self) -> Path:
        """获取当天的日志文件路径（自动切换日期）"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self._current_date != today:
            self._current_date = today
            self._current_file = self.log_dir / f"{today}.txt"
        return self._current_file

    def write(self, event_type: str, details: str = "") -> None:
        """
        写入一条操作日志
        
        Args:
            event_type: 事件类型，如 button_click / emergency_gpio / system_boot
            details: 详情描述
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{timestamp} | {event_type} | {details}\n"

        with self._lock:
            file_path = self._get_file_path()
            try:
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(line)
            except Exception as e:
                # 操作日志写入失败不应影响主程序，但应记录到系统日志
                import logging
                logging.error(f"[OpLog] 写入失败: {e}")

    def log_button_click(self, button_id: str, button_label: str) -> None:
        """记录按钮点击"""
        self.write("button_click", f"{button_id} | {button_label}")

    def log_emergency_gpio(self) -> None:
        """记录物理紧急按钮触发"""
        self.write("emergency_gpio", "物理大红按钮被按下")

    def log_emergency_auto(self, reason: str) -> None:
        """记录自动触发的紧急事件（V2 手环异常等预留）"""
        self.write("emergency_auto", reason)

    def log_system_boot(self) -> None:
        """记录系统启动"""
        self.write("system_boot", "GuardianStar 启动")

    def log_notify_sent(self, channel: str, content: str) -> None:
        """记录通知发送"""
        self.write("notify_sent", f"{channel} | {content}")

    def log_notify_failed(self, channel: str, reason: str) -> None:
        """记录通知发送失败"""
        self.write("notify_failed", f"{channel} | {reason}")

    def log_audio_play(self, filename: str) -> None:
        """记录音频播放"""
        self.write("audio_play", filename)
