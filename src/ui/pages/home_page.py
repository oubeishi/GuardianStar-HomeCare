"""
UI 页面 - 主菜单
仅2个巨型按钮：唠家常（蓝色）、需要帮忙（绿色）
"""
import tkinter as tk
from typing import Callable, Optional

from ...models.button import HOME_BUTTONS
from ...models.button import ButtonModel
from ..widgets.big_button import BigButton
from ..themes import Theme


class HomePage(tk.Frame):
    """
    主菜单页面
    
    布局: 2列网格，每列1个按钮，各占50%宽度、100%高度
    """
    def __init__(
        self,
        parent: tk.Widget,
        on_navigate: Optional[Callable[[str], None]] = None,
        emoji_size: int = 120,
        label_size: int = 48,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.on_navigate = on_navigate
        self.emoji_size = emoji_size
        self.label_size = label_size

        self.configure(bg="black")
        self._build_layout()
        self._create_buttons()

    def _build_layout(self) -> None:
        """构建网格布局：2列等宽，1行等高"""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")

    def _create_buttons(self) -> None:
        """创建两个主菜单按钮"""
        for idx, model in enumerate(HOME_BUTTONS):
            btn = BigButton(
                self,
                model=model,
                emoji_size=self.emoji_size,
                label_size=self.label_size,
                on_click=self._handle_click
            )
            btn.grid(row=0, column=idx, sticky="nsew", padx=10, pady=10)

    def _handle_click(self, model: ButtonModel) -> None:
        """按钮点击处理：触发导航回调"""
        if self.on_navigate:
            self.on_navigate(model.button_id)

    def show(self) -> None:
        """显示页面"""
        self.lift()
        self.focus_set()
