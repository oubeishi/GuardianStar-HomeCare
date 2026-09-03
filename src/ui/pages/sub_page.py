"""
UI 页面 - 二级菜单
2行×3列布局，共6个按钮，铺满屏幕
支持两种子菜单：唠家常(chat)、需要帮忙(help)
"""
import tkinter as tk
from math import ceil
from typing import Callable, Optional, List

from ...models.button import ButtonModel, CHAT_BUTTONS, HELP_BUTTONS
from ..widgets.big_button import BigButton
from ..themes import Theme


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
        on_navigate: Optional[Callable[[str], None]] = None,
        emoji_size: int = 120,
        label_size: int = 48,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.page_type = page_type
        self.on_button_click = on_button_click
        self.on_navigate = on_navigate
        self.emoji_size = emoji_size
        self.label_size = label_size

        self.configure(bg="black")
        self._all_buttons: List[ButtonModel] = CHAT_BUTTONS if page_type == "chat" else HELP_BUTTONS
        self._page_size = 6
        self._page_index = 0
        self._content = tk.Frame(self, bg="black")
        self._content.grid(row=0, column=0, sticky="nsew")
        self._navigation = tk.Frame(self, bg="#20252B", height=96)
        self._navigation.grid(row=1, column=0, sticky="ew")
        self._navigation.grid_propagate(False)

        self._build_layout()
        self._build_navigation()
        self._show_page()

    def _build_layout(self) -> None:
        """构建内容区和底部导航栏"""
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

    def _build_navigation(self) -> None:
        """创建固定在底部的返回和翻页按钮"""
        self._back_button = tk.Button(
            self._navigation,
            text="↩️  返回首页",
            command=lambda: self._navigate("home"),
            **self._navigation_style("#A9A9A9")
        )
        self._back_button.pack(side="left", fill="y", padx=(12, 6), pady=12)

        self._next_button = tk.Button(
            self._navigation,
            text="下一页  ▶",
            command=lambda: self._change_page(1),
            **self._navigation_style("#4169E1")
        )
        self._next_button.pack(side="right", fill="y", padx=(6, 12), pady=12)

        self._previous_button = tk.Button(
            self._navigation,
            text="◀  上一页",
            command=lambda: self._change_page(-1),
            **self._navigation_style("#4169E1")
        )
        self._previous_button.pack(side="right", fill="y", padx=6, pady=12)

        self._page_label = tk.Label(
            self._navigation,
            font=Theme.get_font(24, bold=True),
            bg="#20252B",
            fg="white"
        )
        self._page_label.pack(side="right", expand=True)

    def _show_page(self) -> None:
        """渲染当前页内容，并更新导航状态"""
        for child in self._content.winfo_children():
            child.destroy()

        for r in range(2):
            self._content.grid_rowconfigure(r, weight=1, uniform="row")
        for c in range(3):
            self._content.grid_columnconfigure(c, weight=1, uniform="col")

        start = self._page_index * self._page_size
        page_buttons = self._all_buttons[start:start + self._page_size]
        for idx, model in enumerate(page_buttons):
            row = idx // 3
            col = idx % 3
            btn = BigButton(
                self._content,
                model=model,
                emoji_size=self.emoji_size,
                label_size=self.label_size,
                on_click=self._handle_click
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        page_count = max(1, ceil(len(self._all_buttons) / self._page_size))
        self._page_label.configure(text=f"第 {self._page_index + 1} / {page_count} 页")
        self._previous_button.configure(state="normal" if self._page_index > 0 else "disabled")
        self._next_button.configure(state="normal" if self._page_index < page_count - 1 else "disabled")

    @staticmethod
    def _navigation_style(bg_color: str) -> dict:
        """返回底部导航按钮样式"""
        return {
            "bg": bg_color,
            "fg": "white",
            "activebackground": Theme._darken(bg_color),
            "activeforeground": "white",
            "font": Theme.get_font(24, bold=True),
            "borderwidth": 0,
            "highlightthickness": 0,
            "relief": "flat",
            "padx": 24,
        }

    def _change_page(self, offset: int) -> None:
        """切换内容页"""
        page_count = max(1, ceil(len(self._all_buttons) / self._page_size))
        self._page_index = max(0, min(self._page_index + offset, page_count - 1))
        self._show_page()

    def _navigate(self, target: str) -> None:
        """触发页面导航"""
        if self.on_navigate:
            self.on_navigate(target)

    def _handle_click(self, model: ButtonModel) -> None:
        """按钮点击：回调给上层处理"""
        if self.on_button_click:
            self.on_button_click(model)

    def show(self) -> None:
        """显示页面"""
        self.lift()
        self.focus_set()
