"""
数据模型层 - 按钮定义
V1 固定词库的数据结构，支持未来扩展（V4 双语等）
"""
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass(frozen=True)
class ButtonModel:
    """
    按钮数据模型
    
    Attributes:
        button_id: 唯一标识符，用于日志和配置匹配
        emoji: 显示的 Emoji 图标
        label: 底部文字标签（中文）
        bg_color: 背景色（Hex 字符串，如 #87CEEB）
        sound_file: 对应的音频文件名（不含路径）
        is_emergency: 是否为紧急按钮（触发通知）
        is_nav: 是否为导航按钮（仅界面跳转，无音频）
        action_callback: 可选的自定义回调函数（预留，V1 不用）
    """
    button_id: str
    emoji: str
    label: str
    bg_color: str
    sound_file: Optional[str] = None
    is_emergency: bool = False
    is_nav: bool = False
    action_callback: Optional[Callable] = None

    def __repr__(self) -> str:
        return f"ButtonModel(id={self.button_id}, label={self.label})"


# V1 固定词库：唠家常（蓝色入口）
CHAT_BUTTONS = [
    ButtonModel("son", "👨", "想儿子", "#87CEEB", "son.wav"),
    ButtonModel("daughter", "👩", "想女儿", "#FFB6C1", "daughter.wav"),
    ButtonModel("time", "🕐", "几点了", "#FFFACD", "time.wav"),
    ButtonModel("eat", "🍚", "吃饭", "#98FB98", "eat.wav"),
    ButtonModel("situp", "🪑", "坐起来", "#87CEFA", "situp.wav"),
    ButtonModel("call", "📞", "打电话", "#DDA0DD", "call.wav"),
    ButtonModel("sleep", "😴", "想睡觉", "#B0C4DE", "sleep.wav"),
    ButtonModel("medicine", "💊", "吃药", "#F0E68C", "medicine.wav"),
    ButtonModel("tv", "📺", "想看电视", "#AFEEEE", "tv.wav"),
    ButtonModel("family", "👪", "想家人", "#FFDAB9", "family.wav"),
    ButtonModel("thanks", "🙏", "谢谢你", "#D8BFD8", "thanks.wav"),
    ButtonModel("goodnight", "🌙", "晚安", "#778899", "goodnight.wav"),
]

# V1 固定词库：需要帮忙（绿色入口）
HELP_BUTTONS = [
    ButtonModel("water", "💧", "喝水", "#4169E1", "water.wav"),
    ButtonModel("turn", "🛏️", "翻身", "#32CD32", "turn.wav"),
    ButtonModel("toilet", "🚽", "小便", "#FFD700", "toilet.wav"),
    ButtonModel("pain", "🔥", "疼/难受", "#FF0000", "pain.wav", is_emergency=True),
    ButtonModel("hotcold", "🌡️", "热/冷", "#FFA500", "hotcold.wav"),
]

# 主菜单入口按钮
HOME_BUTTONS = [
    ButtonModel("chat", "👤", "唠家常", "#4169E1"),
    ButtonModel("help", "🙋", "需要帮忙", "#32CD32"),
]

# 所有按钮的字典索引，便于通过 ID 快速查找
ALL_BUTTONS_MAP = {b.button_id: b for b in CHAT_BUTTONS + HELP_BUTTONS + HOME_BUTTONS}
