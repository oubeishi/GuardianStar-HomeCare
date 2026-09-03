"""
GPIO 物理紧急按钮模块
检测 GPIO17 下降沿中断，软件防抖 50ms
V1: 单按钮；V2+: 可扩展为传感器阵列
"""
import logging
import threading
import time
from typing import Callable, Optional

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
    logging.warning("[GPIO] RPi.GPIO 未安装，GPIO功能将不可用（非树莓派环境）")

logger = logging.getLogger(__name__)


class EmergencyButton:
    """
    物理紧急按钮控制器
    
    特性:
        - 下降沿中断触发（按下瞬间）
        - 软件防抖（默认 50ms）
        - 线程安全
        - 支持非树莓派环境的模拟模式（测试用）
    """
    def __init__(self, pin: int = 17, debounce_ms: int = 50, pull_up: bool = True):
        self.pin = pin
        self.debounce_ms = debounce_ms
        self.pull_up = pull_up
        self._callback: Optional[Callable[[], None]] = None
        self._last_trigger_time = 0.0
        self._lock = threading.Lock()
        self._simulation_mode = GPIO is None
        self._running = False

        if not self._simulation_mode:
            self._setup_gpio()
        else:
            logger.warning("[GPIO] 运行在模拟模式（非树莓派环境），GPIO按钮无效")

    def _setup_gpio(self) -> None:
        """初始化 GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)
            pull = GPIO.PUD_UP if self.pull_up else GPIO.PUD_DOWN
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=pull)
            logger.info(f"[GPIO] 紧急按钮已初始化: GPIO{self.pin}, 上拉={self.pull_up}")
        except Exception as e:
            logger.error(f"[GPIO] 初始化失败: {e}")
            self._simulation_mode = True

    def on_trigger(self, callback: Callable[[], None]) -> None:
        """
        注册触发回调函数
        
        Args:
            callback: 无参数函数，按钮按下时被调用
        """
        self._callback = callback

    def start(self) -> None:
        """开始监听按钮事件"""
        if self._simulation_mode:
            return
        if self._running:
            return
        self._running = True

        try:
            edge = GPIO.FALLING if self.pull_up else GPIO.RISING
            GPIO.add_event_detect(
                self.pin,
                edge,
                callback=self._interrupt_handler,
                bouncetime=self.debounce_ms
            )
            logger.info("[GPIO] 事件检测已启动")
        except Exception as e:
            logger.error(f"[GPIO] 事件检测启动失败: {e}")
            self._running = False

    def stop(self) -> None:
        """停止监听并清理 GPIO"""
        self._running = False
        if not self._simulation_mode:
            try:
                GPIO.remove_event_detect(self.pin)
                GPIO.cleanup(self.pin)
                logger.info("[GPIO] 已清理")
            except Exception as e:
                logger.warning(f"[GPIO] 清理异常: {e}")

    def _interrupt_handler(self, channel: int) -> None:
        """GPIO 中断回调（内部使用）"""
        now = time.time()
        with self._lock:
            # 软件防抖（双重保险）
            if (now - self._last_trigger_time) * 1000 < self.debounce_ms:
                return
            self._last_trigger_time = now

        logger.info(f"[GPIO] 紧急按钮触发! GPIO{channel}")
        if self._callback:
            try:
                self._callback()
            except Exception as e:
                logger.error(f"[GPIO] 回调执行异常: {e}", exc_info=True)

    # --- 模拟模式方法（测试用） ---
    def simulate_press(self) -> None:
        """模拟按钮按下（仅模拟模式或测试时调用）"""
        logger.info("[GPIO] 模拟按钮按下")
        if self._callback:
            self._callback()
