"""
音频播放模块
基于 pygame.mixer，实现抢断式 WAV 播放
支持紧急音频保护（普通音频不可打断紧急音频）
"""
import os
import wave
import logging
from pathlib import Path
from typing import Optional

try:
    import pygame
except ImportError:
    pygame = None
    logging.warning("[Audio] pygame 未安装，音频功能将不可用")

logger = logging.getLogger(__name__)


class AudioPlayer:
    """
    音频播放器（单例建议，但此处允许实例化以便测试）
    
    核心规则:
        1. 普通音频：抢断式，新点击立即中断旧音频
        2. 紧急音频：不可被普通音频打断，只能通过 stop_emergency() 或程序终止停止
    """
    def __init__(self, sounds_dir: str, volume: int = 85):
        self.sounds_dir = Path(os.path.expanduser(sounds_dir))
        self._volume = volume / 100.0  # 0.0 ~ 1.0
        self._emergency_playing = False
        self._initialized = False
        self._current_channel = None

        if pygame is None:
            logger.error("[Audio] pygame 未安装，音频功能不可用")
            return

        try:
            pygame.mixer.init(frequency=16000, size=-16, channels=1, buffer=512)
            pygame.mixer.set_num_channels(2)  # 通道0:普通音频, 通道1:紧急音频（预留）
            self._initialized = True
            logger.info("[Audio] pygame.mixer 初始化成功")
        except Exception as e:
            logger.warning(f"[Audio] pygame.mixer 初始化失败（可能无音频设备）: {e}")
            logger.info("[Audio] 程序将继续运行，但无音频输出")

    def _get_path(self, filename: str) -> Optional[Path]:
        """获取音频文件完整路径"""
        if not filename:
            return None
        path = self.sounds_dir / filename
        if not path.exists():
            logger.error(f"[Audio] 音频文件不存在: {path}")
            return None
        return path

    def _validate_wav(self, path: Path) -> bool:
        """校验 WAV 格式（16bit/16kHz/单声道）"""
        try:
            with wave.open(str(path), "rb") as wf:
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                if channels != 1 or sampwidth != 2 or framerate != 16000:
                    logger.warning(
                        f"[Audio] 格式不匹配: {path.name} "
                        f"(channels={channels}, width={sampwidth}, rate={framerate})，"
                        f"期望 (1, 2, 16000)"
                    )
                    return False
            return True
        except Exception as e:
            logger.error(f"[Audio] 无法解析 WAV: {path.name} - {e}")
            return False

    def play(self, filename: str, is_emergency: bool = False) -> bool:
        """
        播放音频文件
        
        Args:
            filename: 音频文件名（不含路径）
            is_emergency: 是否为紧急音频
        
        Returns:
            是否成功开始播放
        """
        if pygame is None or not self._initialized:
            logger.debug(f"[Audio] 音频不可用，跳过播放: {filename}")
            return False

        # 紧急音频保护：普通音频不能打断紧急音频
        if not is_emergency and self._emergency_playing:
            logger.info("[Audio] 紧急音频播放中，普通音频被忽略")
            return False

        path = self._get_path(filename)
        if path is None:
            return False

        # 格式校验（可选）
        if not self._validate_wav(path):
            # 格式不匹配也尝试播放，仅警告
            pass

        try:
            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(self._volume)

            # 抢断式播放
            if is_emergency:
                pygame.mixer.stop()  # 停止所有通道
                self._emergency_playing = True
                logger.info(f"[Audio] 播放紧急音频: {filename}")
            else:
                pygame.mixer.stop()
                logger.info(f"[Audio] 播放音频: {filename}")

            self._current_channel = sound.play()
            return True
        except Exception as e:
            logger.error(f"[Audio] 播放失败: {filename} - {e}")
            return False

    def stop(self) -> None:
        """停止当前播放（仅限非紧急音频上下文使用）"""
        if pygame and self._initialized and not self._emergency_playing:
            pygame.mixer.stop()
            logger.debug("[Audio] 停止播放")

    def stop_emergency(self) -> None:
        """停止紧急音频播放（警报解除时调用）"""
        if pygame and self._initialized:
            pygame.mixer.stop()
            self._emergency_playing = False
            logger.info("[Audio] 紧急音频已停止")

    def is_emergency_playing(self) -> bool:
        """是否有紧急音频正在播放"""
        return self._emergency_playing

    @property
    def is_playing(self) -> bool:
        """是否有音频正在播放"""
        if pygame is None or not self._initialized:
            return False
        return pygame.mixer.get_busy()
