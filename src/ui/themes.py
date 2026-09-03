"""
UI 主题与样式配置
集中管理颜色、字体、尺寸，便于适配不同屏幕和V4无障碍改造
"""
from typing import Dict


class Theme:
    """
    GuardianStar 视觉主题
    
    设计原则:
        - 高对比度：适配老花眼
        - 零文字依赖：颜色+Emoji为主
        - 情绪色明确：蓝色=平和, 绿色=日常, 红色=紧急
    """
    # 主菜单入口色
    HOME_CHAT_BG = "#4169E1"      # 唠家常 - 皇家蓝
    HOME_HELP_BG = "#32CD32"      # 需要帮忙 - 酸橙绿

    # 闪屏颜色
    FLASH_NORMAL = "#90EE90"      # 常规按钮闪屏 - 浅绿
    FLASH_EMERGENCY = "#FF0000"   # 紧急按钮闪屏 - 纯红
    FLASH_OVERLAY_ALPHA = 0.7     # 覆盖层透明度

    # 紧急警报窗
    ALERT_BG = "#8B0000"          # 深红背景
    ALERT_TEXT = "#FFFFFF"        # 白色文字

    # 字体配置（Tkinter 支持的中文字体）
    FONT_FAMILY = "Microsoft YaHei"  # Windows / 部分 Linux
    FONT_FAMILY_FALLBACK = "SimHei"  # 备用黑体

    @classmethod
    def get_font(cls, size: int, bold: bool = False) -> tuple:
        """
        获取字体元组 (family, size, weight)
        
        Tkinter 字体格式: ("Microsoft YaHei", 48, "bold")
        """
        weight = "bold" if bold else "normal"
        return (cls.FONT_FAMILY, size, weight)

    @classmethod
    def get_button_style(cls, bg_color: str) -> Dict:
        """
        获取按钮样式字典
        
        Returns:
            Tkinter Button 可用参数的字典
        """
        return {
            "bg": bg_color,
            "fg": "#FFFFFF" if bg_color in ["#FF0000", "#8B0000", "#4169E1", "#32CD32"] else "#333333",
            "activebackground": cls._darken(bg_color),
            "activeforeground": "#FFFFFF",
            "borderwidth": 0,
            "highlightthickness": 0,
            "relief": "flat",
            "cursor": "hand2",
        }

    @staticmethod
    def _darken(hex_color: str, factor: float = 0.8) -> str:
        """将颜色加深（用于 active 状态）"""
        hex_color = hex_color.lstrip("#")
        r = max(0, int(int(hex_color[0:2], 16) * factor))
        g = max(0, int(int(hex_color[2:4], 16) * factor))
        b = max(0, int(int(hex_color[4:6], 16) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
