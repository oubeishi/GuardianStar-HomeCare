"""
UI 主窗口管理
负责：全屏窗口、页面栈管理（主菜单↔二级菜单）、紧急警报弹窗
"""
import tkinter as tk
from typing import Optional

from .pages.home_page import HomePage
from .pages.sub_page import SubPage
from .widgets.flash_overlay import FlashOverlay
from .themes import Theme


class MainWindow:
    """
    应用主窗口
    
    职责:
        1. 创建 Tk 全屏根窗口
        2. 管理页面：HomePage, SubPage(chat), SubPage(help)
        3. 处理页面切换动画（V1 直接切换，V3 可扩展淡入淡出）
        4. 显示紧急警报弹窗（Toplevel）
    """
    def __init__(
        self,
        width: int = 1920,
        height: int = 1280,
        fullscreen: bool = True,
        cursor_hide: bool = True,
        flash_duration_ms: int = 800,
        emoji_size: int = 120,
        label_size: int = 48,
        emergency_emoji_size: int = 200
    ):
        self._width = width
        self._height = height
        self._flash_duration_ms = flash_duration_ms
        self._emoji_size = emoji_size
        self._label_size = label_size
        self._emergency_emoji_size = emergency_emoji_size

        self._root = tk.Tk()
        self._setup_window(fullscreen, cursor_hide)

        # 页面容器
        self._container = tk.Frame(self._root, bg="black")
        self._container.pack(fill="both", expand=True)

        # 页面实例（懒加载或预创建）
        self._home_page: Optional[HomePage] = None
        self._chat_page: Optional[SubPage] = None
        self._help_page: Optional[SubPage] = None
        self._current_page_id: str = "home"

        # 紧急弹窗引用
        self._emergency_dialog: Optional[tk.Toplevel] = None

        # 导航回调（由 App 层注入）
        self.on_navigate: Optional[callable] = None
        self.on_button_click: Optional[callable] = None
        self.on_emergency_dismiss: Optional[callable] = None

        self._build_pages()

    def _setup_window(self, fullscreen: bool, cursor_hide: bool) -> None:
        """配置窗口属性"""
        self._root.title("奶奶的守护星")
        self._root.configure(bg="black")

        if fullscreen:
            self._root.attributes("-fullscreen", True)
        else:
            self._root.geometry(f"{self._width}x{self._height}")
            self._root.resizable(False, False)

        if cursor_hide:
            self._root.configure(cursor="none")

        # 绑定退出快捷键（调试用：Esc 退出全屏，Ctrl+Q 退出程序）
        self._root.bind("<Escape>", lambda e: self._root.attributes("-fullscreen", False))
        self._root.bind("<Control-q>", lambda e: self.quit())

    def _build_pages(self) -> None:
        """构建所有页面"""
        # 主菜单
        self._home_page = HomePage(
            self._container,
            on_navigate=self._on_home_navigate,
            emoji_size=self._emoji_size,
            label_size=self._label_size
        )
        self._home_page.place(relwidth=1.0, relheight=1.0)

        # 唠家常二级菜单
        self._chat_page = SubPage(
            self._container,
            page_type="chat",
            on_button_click=self._on_sub_button_click,
            emoji_size=self._emoji_size,
            label_size=self._label_size
        )
        self._chat_page.place(relwidth=1.0, relheight=1.0)

        # 需要帮忙二级菜单
        self._help_page = SubPage(
            self._container,
            page_type="help",
            on_button_click=self._on_sub_button_click,
            emoji_size=self._emoji_size,
            label_size=self._label_size
        )
        self._help_page.place(relwidth=1.0, relheight=1.0)

        # 默认显示首页
        self.show_page("home")

    def _on_home_navigate(self, button_id: str) -> None:
        """主菜单导航回调"""
        if button_id == "chat":
            self.show_page("chat")
        elif button_id == "help":
            self.show_page("help")
        # 通知 App 层（如有额外处理）
        if self.on_navigate:
            self.on_navigate(button_id)

    def _on_sub_button_click(self, model) -> None:
        """二级菜单按钮点击回调"""
        if model.button_id == "back":
            self.show_page("home")
            return
        if self.on_button_click:
            self.on_button_click(model)

    def show_page(self, page_id: str) -> None:
        """
        切换页面
        
        Args:
            page_id: "home" | "chat" | "help"
        """
        self._current_page_id = page_id
        if page_id == "home" and self._home_page:
            self._home_page.show()
        elif page_id == "chat" and self._chat_page:
            self._chat_page.show()
        elif page_id == "help" and self._help_page:
            self._help_page.show()

    def show_flash(self, emoji: str = "✅", is_emergency: bool = False) -> None:
        """
        显示闪屏反馈
        
        Args:
            emoji: 显示的 Emoji
            is_emergency: 是否为紧急状态（红色背景）
        """
        bg = Theme.FLASH_EMERGENCY if is_emergency else Theme.FLASH_NORMAL
        overlay = FlashOverlay(
            self._root,
            emoji=emoji,
            bg_color=bg,
            duration_ms=self._flash_duration_ms,
            emoji_size=self._emergency_emoji_size if is_emergency else self._emoji_size
        )
        overlay.show()

    def show_emergency_alert(self) -> None:
        """
        显示全屏紧急警报弹窗（无边框、红色、居中大字）
        点击任意位置关闭
        """
        if self._emergency_dialog is not None:
            return  # 已有弹窗，避免重复

        dialog = tk.Toplevel(self._root)
        dialog.overrideredirect(True)
        dialog.attributes("-topmost", True)
        dialog.configure(bg=Theme.ALERT_BG)

        # 全屏覆盖
        dialog.geometry(f"{self._width}x{self._height}+0+0")

        # 中央内容
        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_columnconfigure(0, weight=1)

        content = tk.Frame(dialog, bg=Theme.ALERT_BG)
        content.grid(row=0, column=0)

        emoji_label = tk.Label(
            content,
            text="🚨",
            font=("Segoe UI Emoji", self._emergency_emoji_size),
            bg=Theme.ALERT_BG,
            fg="white"
        )
        emoji_label.pack()

        text_label = tk.Label(
            content,
            text="紧急求救",
            font=Theme.get_font(80, bold=True),
            bg=Theme.ALERT_BG,
            fg=Theme.ALERT_TEXT
        )
        text_label.pack(pady=20)

        hint_label = tk.Label(
            content,
            text="点击屏幕任意位置关闭",
            font=Theme.get_font(24),
            bg=Theme.ALERT_BG,
            fg="#CCCCCC"
        )
        hint_label.pack()

        # 点击关闭
        def _dismiss(event=None):
            dialog.destroy()
            self._emergency_dialog = None
            if self.on_emergency_dismiss:
                self.on_emergency_dismiss()

        for widget in (dialog, content, emoji_label, text_label, hint_label):
            widget.bind("<Button-1>", _dismiss)

        self._emergency_dialog = dialog
        dialog.grab_set()

    def close_emergency_alert(self) -> None:
        """主动关闭紧急弹窗（如程序复位时）"""
        if self._emergency_dialog is not None:
            try:
                self._emergency_dialog.destroy()
            except Exception:
                pass
            self._emergency_dialog = None

    def run(self) -> None:
        """启动 Tkinter 主循环"""
        self._root.mainloop()

    def quit(self) -> None:
        """退出应用"""
        self._root.quit()
        self._root.destroy()
