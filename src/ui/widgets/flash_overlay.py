"""
UI 组件 - 闪屏覆盖层
点击按钮后全屏显示反馈（绿色✅ 或 红色🚨），0.8秒后自动消失
闪屏期间禁用底层交互（防连击）
"""
import tkinter as tk
from typing import Optional

from ..themes import Theme


class FlashOverlay(tk.Toplevel):
    """
    闪屏覆盖层窗口
    
    使用 Toplevel 覆盖全屏，相比 Canvas 覆盖层更轻量
    显示期间通过 grab_set() 拦截所有事件
    """
    def __init__(
        self,
        parent: tk.Tk,
        emoji: str = "✅",
        bg_color: str = Theme.FLASH_NORMAL,
        duration_ms: int = 800,
        emoji_size: int = 200
    ):
        super().__init__(parent)
        self.duration_ms = duration_ms
        self._setup_window(parent, bg_color)
        self._build_ui(emoji, bg_color, emoji_size)

    def _setup_window(self, parent: tk.Tk, bg_color: str) -> None:
        """配置窗口属性：无边框、全屏、置顶"""
        self.overrideredirect(True)           # 无边框
        self.attributes("-topmost", True)     # 置顶
        self.attributes("-alpha", Theme.FLASH_OVERLAY_ALPHA)  # 半透明
        self.configure(bg=bg_color)

        # 尺寸与位置：覆盖整个父窗口
        parent.update_idletasks()
        x = parent.winfo_x()
        y = parent.winfo_y()
        w = parent.winfo_width()
        h = parent.winfo_height()
        self.geometry(f"{w}x{h}+{x}+{y}")

        # 拦截所有输入事件（防止闪屏期间点击穿透）
        self.grab_set()

    def _build_ui(self, emoji: str, bg_color: str, emoji_size: int) -> None:
        """构建中央 Emoji"""
        self.configure(bg=bg_color)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        label = tk.Label(
            self,
            text=emoji,
            font=("Segoe UI Emoji", emoji_size),
            bg=bg_color,
            fg="white"
        )
        label.grid(row=0, column=0)

    def show(self) -> None:
        """显示闪屏，并在 duration_ms 后自动关闭"""
        self.deiconify()
        self.after(self.duration_ms, self.destroy)

    def destroy(self) -> None:
        """释放 grab 并销毁窗口"""
        try:
            self.grab_release()
        except Exception:
            pass
        super().destroy()
