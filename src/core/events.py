"""
事件总线模块
实现轻量级发布-订阅模式，用于解耦各模块（音频、UI、GPIO、通知、日志）
V1 基础版；V2/V3 可扩展更多事件类型
"""
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    全局事件总线（单例模式）
    
    事件命名规范:
        button.clicked     - 按钮被点击（payload: ButtonModel）
        button.pressed     - 物理按钮被按下（payload: dict）
        audio.play         - 请求播放音频（payload: str 文件路径）
        audio.stop         - 请求停止音频
        flash.show         - 显示闪屏（payload: dict {emoji, color}）
        flash.hide         - 隐藏闪屏
        notify.send        - 发送通知（payload: str 消息内容）
        emergency.trigger  - 紧急状态触发
        emergency.clear    - 紧急状态解除
        log.write          - 写入操作日志（payload: dict）
        app.shutdown       - 应用关闭
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners: Dict[str, List[Callable]] = {}
        return cls._instance

    def subscribe(self, event_name: str, callback: Callable[[Any], None]) -> None:
        """订阅事件"""
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)
        logger.debug(f"[EventBus] 订阅事件: {event_name}")

    def unsubscribe(self, event_name: str, callback: Callable[[Any], None]) -> None:
        """取消订阅"""
        if event_name in self._listeners:
            try:
                self._listeners[event_name].remove(callback)
            except ValueError:
                pass

    def publish(self, event_name: str, payload: Any = None) -> None:
        """发布事件（异步回调，异常隔离）"""
        if event_name not in self._listeners:
            return
        for callback in self._listeners[event_name]:
            try:
                callback(payload)
            except Exception as e:
                logger.error(f"[EventBus] 事件 {event_name} 处理异常: {e}", exc_info=True)
                # 异常隔离：一个回调出错不影响其他回调


# 全局事件总线实例
event_bus = EventBus()
