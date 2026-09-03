#!/usr/bin/env bash
# GuardianStar 开机自启脚本（systemd service 调用此脚本）
# 安装路径: /usr/local/bin/guardianstar.sh
# 配合 /etc/systemd/system/guardianstar.service 使用

set -e

# 等待图形界面就绪
sleep 5

# 强制音频走 3.5mm
amixer cset numid=3 1 2>/dev/null || true

# 设置音量
amixer set PCM -- 85% 2>/dev/null || true

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"

# 若未找到，尝试默认路径
if [ ! -f "${PROJECT_DIR}/src/main.py" ]; then
    PROJECT_DIR="/home/pi/GuardianStar-HomeCare"
fi

# 导出 DISPLAY 环境变量
export DISPLAY=:0
export XAUTHORITY="/home/pi/.Xauthority"

# 进入项目目录
cd "${PROJECT_DIR}"

# 启动主程序
exec /usr/bin/python3 "${PROJECT_DIR}/src/main.py"
