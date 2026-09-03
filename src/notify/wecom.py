"""
企业微信群机器人通知模块
基于官方 Webhook 接口，HTTP POST 发送文本/Markdown消息
"""
import logging
import requests
from typing import Any, List, Optional

from .base import BaseNotifier

logger = logging.getLogger(__name__)


class WeComNotifier(BaseNotifier):
    """
    企业微信群机器人通知器
    
    配置项（来自 config.json wecom 段）:
        - enabled: 是否启用
        - webhook_url: 完整的 Webhook 地址，含 key 参数
        - mentioned_mobile_list: @提醒的手机号列表（可选）
        - timeout_seconds: HTTP 超时时间
        - retry_times: 失败重试次数
    """
    def __init__(self, webhook_url: str, enabled: bool = True,
                 mentioned_mobile_list: Optional[List[str]] = None,
                 timeout: int = 5, retry: int = 1):
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.mentioned_mobile_list = mentioned_mobile_list or []
        self.timeout = timeout
        self.retry = retry

    def is_available(self) -> bool:
        """检查是否已启用且配置了 Webhook"""
        return self.enabled and bool(self.webhook_url) and "YOUR_KEY" not in self.webhook_url

    def send(self, message: str, **kwargs: Any) -> bool:
        """
        发送文本消息到企业微信群
        
        Args:
            message: 消息内容
            **kwargs:
                - is_markdown: bool，是否使用 Markdown 格式（默认 False）
                - mentioned_mobile_list: List[str]，临时覆盖 @列表
        """
        if not self.is_available():
            logger.debug("[WeCom] 通知渠道未启用或未配置，跳过发送")
            return False

        is_markdown = kwargs.get("is_markdown", False)
        mobiles = kwargs.get("mentioned_mobile_list", self.mentioned_mobile_list)

        payload = self._build_payload(message, is_markdown, mobiles)

        for attempt in range(self.retry + 1):
            try:
                resp = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )
                resp.raise_for_status()
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info(f"[WeCom] 通知发送成功: {message[:30]}...")
                    return True
                else:
                    logger.warning(f"[WeCom] 发送失败: {result}")
            except requests.exceptions.Timeout:
                logger.warning(f"[WeCom] 请求超时（尝试 {attempt + 1}/{self.retry + 1}）")
            except requests.exceptions.RequestException as e:
                logger.warning(f"[WeCom] 请求异常（尝试 {attempt + 1}/{self.retry + 1}）: {e}")
            except Exception as e:
                logger.error(f"[WeCom] 未知异常: {e}")

        logger.error("[WeCom] 通知发送失败，已耗尽重试次数")
        return False

    def _build_payload(self, message: str, is_markdown: bool, mobiles: List[str]) -> dict:
        """构建请求体"""
        msg_type = "markdown" if is_markdown else "text"
        payload = {
            "msgtype": msg_type,
        }
        if is_markdown:
            payload["markdown"] = {"content": message}
        else:
            payload["text"] = {
                "content": message,
                "mentioned_mobile_list": mobiles,
            }
        return payload
