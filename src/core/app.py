"""
应用主控模块 (App Controller)
协调所有子模块：配置、日志、音频、通知、GPIO、UI
V1 核心 orchestrator；V2/V3/V4 在此扩展新模块集成
"""
import logging
import os
import sys
from datetime import datetime

from .config import config
from .logger import setup_logging
from .events import event_bus

from ..audio.player import AudioPlayer
from ..notify.wecom import WeComNotifier
from ..notify.base import MultiNotifier
from ..hardware.gpio_button import EmergencyButton
from ..hardware.sensors import SensorManager
from ..data.log_manager import OperationLogManager
from ..ui.main_window import MainWindow
from ..models.button import ButtonModel

logger = logging.getLogger(__name__)


class GuardianStarApp:
    """
    GuardianStar 应用程序主控类
    
    生命周期:
        1. __init__()   - 配置加载
        2. initialize() - 初始化所有子模块
        3. run()        - 启动主循环
        4. shutdown()   - 优雅退出
    """
    def __init__(self):
        self._running = False
        self.audio: AudioPlayer = None
        self.notifier: MultiNotifier = None
        self.op_log: OperationLogManager = None
        self.gpio_btn: EmergencyButton = None
        self.window: MainWindow = None
        self.sensors: SensorManager = None

    def initialize(self, config_path: str = None) -> bool:
        """
        初始化所有子模块
        
        Returns:
            bool: 是否初始化成功（失败也应尽量继续运行）
        """
        try:
            # 1. 加载配置
            config.load(config_path)

            # 2. 初始化系统日志
            setup_logging(
                log_dir=config.get("logging.dir", "~/guardian_star/logs"),
                level=config.get("logging.level", "INFO"),
                console=config.get("logging.console_output", False)
            )
            logger.info("=" * 50)
            logger.info("GuardianStar 正在启动...")

            # 3. 初始化操作日志
            self.op_log = OperationLogManager(config.get("logging.dir", "~/guardian_star/logs"))
            self.op_log.log_system_boot()

            # 4. 初始化音频播放器
            self.audio = AudioPlayer(
                sounds_dir=config.get("audio.sounds_dir", "~/guardian_star/sounds"),
                volume=config.get("audio.volume", 85)
            )

            # 5. 初始化通知系统
            self.notifier = MultiNotifier()
            wecom = WeComNotifier(
                webhook_url=config.get("wecom.webhook_url", ""),
                enabled=config.get("wecom.enabled", True),
                mentioned_mobile_list=config.get("wecom.mentioned_mobile_list", []),
                timeout=config.get("wecom.timeout_seconds", 5),
                retry=config.get("wecom.retry_times", 1)
            )
            self.notifier.add(wecom)

            # 6. 初始化传感器管理器（V1 空壳，V2+ 注册实际传感器）
            self.sensors = SensorManager()

            # 7. 初始化 GPIO 紧急按钮
            self.gpio_btn = EmergencyButton(
                pin=config.get("gpio.emergency_button", 17),
                debounce_ms=config.get("gpio.debounce_ms", 50),
                pull_up=config.get("gpio.pull_up", True)
            )
            self.gpio_btn.on_trigger(self._on_gpio_emergency)
            self.gpio_btn.start()

            # 8. 初始化 UI 主窗口
            self.window = MainWindow(
                width=config.get("display.width", 1920),
                height=config.get("display.height", 1280),
                fullscreen=config.get("display.fullscreen", True),
                cursor_hide=config.get("display.cursor_hide", True),
                flash_duration_ms=config.get("ui.flash_duration_ms", 800),
                emoji_size=config.get("ui.button_emoji_size", 120),
                label_size=config.get("ui.button_label_size", 48),
                emergency_emoji_size=config.get("ui.emergency_emoji_size", 200)
            )
            self.window.on_button_click = self._on_ui_button_click
            self.window.on_emergency_dismiss = self._on_emergency_dismiss

            # 9. 订阅事件总线（扩展点：其他模块可通过事件总线触发动作）
            event_bus.subscribe("audio.play", self._evt_audio_play)
            event_bus.subscribe("audio.stop", self._evt_audio_stop)
            event_bus.subscribe("notify.send", self._evt_notify_send)
            event_bus.subscribe("emergency.trigger", self._evt_emergency_trigger)
            event_bus.subscribe("emergency.clear", self._evt_emergency_clear)

            logger.info("GuardianStar 初始化完成")
            return True

        except Exception as e:
            # 初始化异常不应导致程序崩溃，尽量记录并继续
            print(f"初始化异常: {e}", file=sys.stderr)
            logging.error(f"[App] 初始化异常: {e}", exc_info=True)
            return False

    def run(self) -> None:
        """启动应用主循环"""
        self._running = True
        logger.info("[App] 进入主循环")
        self.window.run()
        self._running = False

    def shutdown(self) -> None:
        """优雅退出，清理资源"""
        logger.info("[App] 正在关闭...")
        self._running = False

        try:
            if self.gpio_btn:
                self.gpio_btn.stop()
        except Exception as e:
            logger.error(f"[App] GPIO 清理异常: {e}")

        try:
            if self.sensors:
                self.sensors.stop_all()
        except Exception as e:
            logger.error(f"[App] 传感器清理异常: {e}")

        try:
            if self.window:
                self.window.quit()
        except Exception as e:
            logger.error(f"[App] UI 清理异常: {e}")

        logger.info("[App] 已关闭")

    # ------------------------------------------------------------------
    # UI 回调处理
    # ------------------------------------------------------------------
    def _on_ui_button_click(self, model: ButtonModel) -> None:
        """
        二级菜单按钮点击处理
        
        处理流程:
            1. 记录操作日志
            2. 播放音频（非导航按钮）
            3. 显示闪屏
            4. 紧急按钮发送通知
        """
        logger.info(f"[App] 按钮点击: {model.label} ({model.button_id})")
        self.op_log.log_button_click(model.button_id, model.label)

        # 导航按钮不播放音频、不闪屏
        if model.is_nav:
            return

        # 播放音频（抢断式）
        if model.sound_file:
            self.audio.play(model.sound_file, is_emergency=model.is_emergency)

        # 显示闪屏
        flash_emoji = "🚨" if model.is_emergency else "✅"
        self.window.show_flash(emoji=flash_emoji, is_emergency=model.is_emergency)

        # 紧急按钮发送通知
        if model.is_emergency:
            self._send_emergency_notify(f"【紧急】奶奶按下了「{model.label}」按钮，时间：{datetime.now().strftime('%H:%M:%S')}")

    def _on_gpio_emergency(self) -> None:
        """
        GPIO 物理紧急按钮触发处理
        
        处理流程:
            1. 记录紧急日志
            2. 播放 emergency.wav（循环/最大音量）
            3. 显示全屏红色警报
            4. 发送企业微信通知
        """
        logger.warning("[App] GPIO 紧急按钮被按下!")
        self.op_log.log_emergency_gpio()

        # 播放紧急音频（不可被普通音频打断）
        self.audio.play("emergency.wav", is_emergency=True)

        # 显示紧急警报窗
        self.window.show_emergency_alert()

        # 发送通知
        self._send_emergency_notify(
            f"🚨【物理紧急按钮触发】\n"
            f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"请立即查看奶奶状况！"
        )

    def _on_emergency_dismiss(self) -> None:
        """紧急警报窗被关闭"""
        logger.info("[App] 紧急警报解除")
        self.audio.stop_emergency()

    # ------------------------------------------------------------------
    # 通知辅助
    # ------------------------------------------------------------------
    def _send_emergency_notify(self, message: str) -> None:
        """发送紧急通知（带日志记录）"""
        try:
            success = self.notifier.send(message)
            if success:
                self.op_log.log_notify_sent("wecom", message[:50])
            else:
                self.op_log.log_notify_failed("wecom", "发送返回失败")
        except Exception as e:
            logger.error(f"[App] 通知发送异常: {e}")
            self.op_log.log_notify_failed("wecom", str(e))

    # ------------------------------------------------------------------
    # 事件总线处理器
    # ------------------------------------------------------------------
    def _evt_audio_play(self, payload) -> None:
        """事件：播放音频"""
        if isinstance(payload, dict):
            self.audio.play(payload.get("file"), payload.get("is_emergency", False))
        elif isinstance(payload, str):
            self.audio.play(payload)

    def _evt_audio_stop(self, payload=None) -> None:
        """事件：停止音频"""
        self.audio.stop()

    def _evt_notify_send(self, payload) -> None:
        """事件：发送通知"""
        if isinstance(payload, str):
            self.notifier.send(payload)

    def _evt_emergency_trigger(self, payload=None) -> None:
        """事件：触发紧急状态（供其他模块调用，如 V2 手环异常）"""
        self._on_gpio_emergency()

    def _evt_emergency_clear(self, payload=None) -> None:
        """事件：解除紧急状态"""
        self.window.close_emergency_alert()
        self.audio.stop_emergency()
