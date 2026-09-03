"""
UI 组件 - 巨型按钮
适配触屏的大尺寸按钮，纯色背景 + 超大 Emoji + 文字标签
"""
import tkinter as tk
from typing import Callable, Optional

from ...models.button import ButtonModel
from ..themes import Theme


class BigButton(tk.Frame):
    """
    自定义巨型按钮组件
    
    布局:
        ┌─────────────────────┐
        │                     │
        │      👨 (Emoji)      │  ← 占 60% 高度
        │                     │
        │      想儿子 (Label)   │  ← 占 30% 高度
        │                     │
        └─────────────────────┘
    
    特性:
        - 无边框、无焦点轮廓
        - 触摸反馈（按下颜色变深）
        - 防止连击（点击后 200ms 内不响应）
    """
    def __init__(
        self,
        parent: tk.Widget,
        model: ButtonModel,
        emoji_size: int = 120,
        label_size: int = 48,
        on_click: Optional[Callable[[ButtonModel], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.model = model
        self.on_click = on_click
        self._debounce_ms = 200  # 防连击间隔
        self._locked = False

        # 背景色
        bg = model.bg_color
        self.configure(bg=bg)

        # 使用 Frame 铺满，内部用 Label 实现（比 Button 更易自定义大小）
        self._build_ui(bg, emoji_size, label_size)
        self._bind_events()

    def _build_ui(self, bg: str, emoji_size: int, label_size: int) -> None:
        """构建界面元素"""
        # 使用 grid 布局让内容居中
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Emoji 标签
        self._emoji_label = tk.Label(
            self,
            text=self.model.emoji,
            font=("Segoe UI Emoji", emoji_size),  # Windows/macOS Emoji 字体
            bg=bg,
            fg="white" if self._is_dark_bg(bg) else "#333333"
        )
        self._emoji_label.grid(row=0, column=0, sticky="s", pady=(20, 5))

        # 文字标签
        self._text_label = tk.Label(
            self,
            text=self.model.label,
            font=Theme.get_font(label_size, bold=True),
            bg=bg,
            fg="white" if self._is_dark_bg(bg) else "#333333"
        )
        self._text_label.grid(row=1, column=0, sticky="n", pady=(5, 20))

    def _bind_events(self) -> None:
        """绑定点击事件"""
        for widget in (self, self._emoji_label, self._text_label):
            widget.bind("<Button-1>", self._on_press)
            widget.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event: tk.Event) -> None:
        """按下效果"""
        if self._locked:
            return
        dark = Theme._darken(self.model.bg_color, 0.7)
        self.configure(bg=dark)
        self._emoji_label.configure(bg=dark)
        self._text_label.configure(bg=dark)

    def _on_release(self, event: tk.Event) -> None:
        """释放效果 + 触发回调"""
        if self._locked:
            return
        # 恢复颜色
        self.configure(bg=self.model.bg_color)
        self._emoji_label.configure(bg=self.model.bg_color)
        self._text_label.configure(bg=self.model.bg_color)

        # 触发回调
        if self.on_click:
            self._locked = True
            self.on_click(self.model)
            self.after(self._debounce_ms, self._unlock)

    def _unlock(self) -> None:
        """解锁，允许下次点击"""
        self._locked = False

    @staticmethod
    def _is_dark_bg(hex_color: str) -> bool:
        """判断背景色是否为深色（决定文字用白或黑）"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 128
