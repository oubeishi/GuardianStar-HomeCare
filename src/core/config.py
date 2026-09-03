"""
配置管理模块
负责加载、校验、暴露 config.json 配置
V1 冷加载（重启生效）；V2/V3 可扩展热重载
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    配置管理器（单例）
    
    查找优先级:
        1. 环境变量 GUARDIANSTAR_CONFIG 指定的路径
        2. ~/guardian_star/config.json
        3. 项目根目录的 config.json
    """
    _instance = None
    _config: Dict[str, Any] = {}

    # 默认值（当配置文件中缺失时使用）
    DEFAULTS = {
        "display": {
            "width": 1920,
            "height": 1280,
            "fullscreen": True,
            "cursor_hide": True,
        },
        "audio": {
            "device": "3.5mm",
            "volume": 85,
            "sounds_dir": "~/guardian_star/sounds",
            "format_check": True,
        },
        "gpio": {
            "emergency_button": 17,
            "debounce_ms": 50,
            "pull_up": True,
        },
        "wecom": {
            "enabled": True,
            "webhook_url": "",
            "mentioned_mobile_list": [],
            "timeout_seconds": 5,
            "retry_times": 1,
        },
        "logging": {
            "dir": "~/guardian_star/logs",
            "level": "INFO",
            "console_output": False,
        },
        "ui": {
            "flash_duration_ms": 800,
            "button_emoji_size": 120,
            "button_label_size": 48,
            "emergency_emoji_size": 200,
        },
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, path: Optional[str] = None) -> None:
        """加载配置文件"""
        config_path = self._resolve_path(path)
        logger.info(f"[Config] 加载配置文件: {config_path}")

        if not os.path.exists(config_path):
            logger.warning(f"[Config] 配置文件不存在: {config_path}，使用默认值")
            self._config = self._deep_copy(self.DEFAULTS)
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            self._config = self._merge(self.DEFAULTS, user_config)
            self._validate()
            logger.info("[Config] 配置文件加载成功")
        except json.JSONDecodeError as e:
            logger.error(f"[Config] JSON 解析失败: {e}，使用默认值")
            self._config = self._deep_copy(self.DEFAULTS)
        except Exception as e:
            logger.error(f"[Config] 加载异常: {e}，使用默认值")
            self._config = self._deep_copy(self.DEFAULTS)

    def _resolve_path(self, path: Optional[str]) -> str:
        """解析配置文件路径"""
        if path:
            return os.path.expanduser(path)
        env_path = os.environ.get("GUARDIANSTAR_CONFIG")
        if env_path:
            return os.path.expanduser(env_path)
        home_path = os.path.expanduser("~/guardian_star/config.json")
        if os.path.exists(home_path):
            return home_path
        # 项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent
        return str(project_root / "config.json")

    def _merge(self, default: Dict, user: Dict) -> Dict:
        """深度合并：user 覆盖 default"""
        result = self._deep_copy(default)
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge(result[key], value)
            else:
                result[key] = value
        return result

    def _deep_copy(self, d: Dict) -> Dict:
        """深度拷贝字典"""
        import copy
        return copy.deepcopy(d)

    def _validate(self) -> None:
        """校验必填配置项"""
        wecom = self._config.get("wecom", {})
        if wecom.get("enabled") and not wecom.get("webhook_url"):
            logger.warning("[Config] 企业微信机器人已启用但未配置 webhook_url，通知功能将静默失败")

        sounds_dir = self._config.get("audio", {}).get("sounds_dir", "")
        expanded = os.path.expanduser(sounds_dir)
        if not os.path.exists(expanded):
            logger.warning(f"[Config] 音频目录不存在: {expanded}，请提前创建")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        按路径获取配置值，如 get("display.width") -> 1920
        """
        keys = key_path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    @property
    def raw(self) -> Dict[str, Any]:
        """获取完整配置字典（只读建议，实际可修改）"""
        return self._config


# 全局配置实例
config = ConfigManager()
