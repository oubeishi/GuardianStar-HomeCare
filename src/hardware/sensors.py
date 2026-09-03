"""
传感器模块（预留接口）
V1: 空壳，仅定义接口
V2: 实现 FSR 压力传感器 + ADS1115 读取
V3: 实现 DHT22 温湿度读取
V4: 实现 BLE 腕带倾斜检测
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class BaseSensor(ABC):
    """传感器抽象基类"""
    @abstractmethod
    def read(self) -> dict:
        """读取传感器数据，返回字典"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """传感器是否可用"""
        pass

    def start(self) -> None:
        """启动传感器（可选）"""
        pass

    def stop(self) -> None:
        """停止传感器（可选）"""
        pass


class SensorManager:
    """
    传感器管理器（V1 空壳，V2+ 注册实际传感器）
    """
    def __init__(self):
        self._sensors: list[BaseSensor] = []
        self._callbacks: list[Callable] = []

    def register(self, sensor: BaseSensor) -> None:
        """注册传感器"""
        self._sensors.append(sensor)
        logger.info(f"[Sensor] 注册传感器: {sensor.__class__.__name__}")

    def start_all(self) -> None:
        """启动所有传感器"""
        for sensor in self._sensors:
            if sensor.is_available():
                sensor.start()

    def stop_all(self) -> None:
        """停止所有传感器"""
        for sensor in self._sensors:
            sensor.stop()

    def read_all(self) -> dict:
        """读取所有传感器数据"""
        result = {}
        for sensor in self._sensors:
            if sensor.is_available():
                try:
                    result[sensor.__class__.__name__] = sensor.read()
                except Exception as e:
                    logger.error(f"[Sensor] 读取失败: {e}")
        return result
