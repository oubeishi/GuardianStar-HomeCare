"""
UI 页面 - 二级菜单
2行×3列布局，共6个按钮，铺满屏幕
支持两种子菜单：唠家常(chat)、需要帮忙(help)
"""
import tkinter as tk
from typing import Callable, Optional, List

from ...models.button import ButtonModel, CHAT_BUTTONS, HELP_BUTTONS
from ..widgets.big_button import BigButton


class SubPage(tk.Frame):
    """
    二级菜单页面
    
    布局: 2行×3列网格，每格1个按钮
    支持动态传入按钮列表，复用于"唠家常"和"需要帮忙"
    """
    def __init__(
        self,
        parent: tk.Widget,
        page_type: str,  # "chat" 或 "help"
        on_button_click: Optional[Callable[[ButtonModel], None]] = None,
        emoji_size: int = 120,
        label_size: int = 48,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.page_type = page_type
        self.on_button_click = on_button_click
        self.emoji_size = emoji_size
        self.label_size = label_size

        self.configure(bg="black")
        self._buttons: List[ButtonModel] = CHAT_BUTTONS if page_type == "chat" else HELP_BUTTONS

        self._build_layout()
        self._create_buttons()

    def _build_layout(self) -> None:
        """构建 2行×3列 网格"""
        for r in range(2):
            self.grid_rowconfigure(r, weight=1, uniform="row")
        for c in range(3):
            self.grid_columnconfigure(c, weight=1, uniform="col")

    def _create_buttons(self) -> None:
        """创建6个按钮"""
        for idx, model in enumerate(self._buttons):
            row = idx // 3
            col = idx % 3
            btn = BigButton(
                self,
                model=model,
                emoji_size=self.emoji_size,
                label_size=self.label_size,
                on_click=self._handle_click
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

    def _handle_click(self, model: ButtonModel) -> None:
        """按钮点击：回调给上层处理"""
        if self.on_button_click:
            self.on_button_click(model)

    def show(self) -> None:
        """显示页面"""
        self.lift()
        self.focus_set()
