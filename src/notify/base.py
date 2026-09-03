"""
通知基类模块
定义通知接口，支持多渠道扩展（企业微信、邮件、短信等）
V1: 企业微信机器人
V2+: 可扩展邮件 fallback、短信等
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseNotifier(ABC):
    """
    通知器抽象基类
    
    所有通知渠道（企业微信、邮件、短信）必须实现此接口
    """
    @abstractmethod
    def send(self, message: str, **kwargs: Any) -> bool:
        """
        发送通知
        
        Args:
            message: 通知内容文本
            **kwargs: 扩展参数（如 @手机号列表、markdown格式等）
        
        Returns:
            是否发送成功
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """当前通知渠道是否可用（配置正确、网络正常）"""
        pass


class MultiNotifier:
    """
    多渠道通知器（组合模式）
    
    按优先级依次尝试多个通知渠道，任一成功即返回
    V1 仅企业微信；未来可加入邮件 fallback
    """
    def __init__(self):
        self._notifiers: list[BaseNotifier] = []

    def add(self, notifier: BaseNotifier) -> None:
        """添加通知渠道"""
        self._notifiers.append(notifier)

    def send(self, message: str, **kwargs: Any) -> bool:
        """
        发送通知，依次尝试所有渠道
        
        Returns:
            是否有至少一个渠道发送成功
        """
        success = False
        for notifier in self._notifiers:
            if notifier.is_available():
                try:
                    if notifier.send(message, **kwargs):
                        success = True
                        break  # 任一成功即停止（避免重复打扰）
                except Exception:
                    continue
        return success
