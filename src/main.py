#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GuardianStar-HomeCare 主入口

启动方式:
    python3 src/main.py
    python3 src/main.py --config /path/to/config.json
    python3 src/main.py --windowed   (窗口模式，调试用)

系统要求:
    - Raspberry Pi OS (64位)
    - Python 3.11+
    - Tkinter (通常预装)
    - pygame (音频)
    - RPi.GPIO (GPIO，非树莓派环境自动进入模拟模式)
"""
import argparse
import os
import signal
import sys

# 将项目根目录加入 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.app import GuardianStarApp


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="奶奶的守护星 - GuardianStar HomeCare"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="配置文件路径 (默认: ~/guardian_star/config.json 或项目根目录 config.json)"
    )
    parser.add_argument(
        "--windowed", "-w",
        action="store_true",
        help="窗口模式（非全屏，调试用）"
    )
    parser.add_argument(
        "--simulate-gpio", "-s",
        action="store_true",
        help="模拟 GPIO 模式（非树莓派环境测试用）"
    )
    return parser.parse_args()


def main() -> int:
    """主函数"""
    args = parse_args()

    # 窗口模式覆盖配置（仅当命令行显式指定时）
    if args.windowed:
        os.environ["GUARDIANSTAR_WINDOWED"] = "1"

    app = GuardianStarApp()

    # 信号处理：优雅退出（SIGINT Ctrl+C, SIGTERM systemd stop）
    def signal_handler(signum, frame):
        print("\n收到退出信号，正在关闭...")
        app.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 初始化
    if not app.initialize(config_path=args.config):
        print("初始化失败，尝试以最小模式启动...", file=sys.stderr)
        # 即使初始化失败也尝试启动 UI，保证奶奶至少能看到界面

    # 运行主循环
    try:
        app.run()
    except Exception as e:
        print(f"运行时异常: {e}", file=sys.stderr)
        return 1
    finally:
        app.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
