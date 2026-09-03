#!/usr/bin/env bash
# GuardianStar systemd 服务安装脚本
# 用法: sudo bash install_service.sh

set -e

SERVICE_NAME="guardianstar.service"
SERVICE_SRC="systemd/guardianstar.service"
SERVICE_DST="/etc/systemd/system/${SERVICE_NAME}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "========================================"
echo "GuardianStar systemd 服务安装"
echo "========================================"

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "错误: 请使用 sudo 运行此脚本"
    exit 1
fi

# 检查服务文件
if [ ! -f "${PROJECT_DIR}/${SERVICE_SRC}" ]; then
    echo "错误: 未找到服务文件 ${SERVICE_SRC}"
    exit 1
fi

# 替换工作目录路径为实际路径
sed -e "s|/home/pi/GuardianStar-HomeCare|${PROJECT_DIR}|g" \
    -e "s|User=pi|User=${SUDO_USER:-pi}|g" \
    -e "s|/home/pi/.Xauthority|/home/${SUDO_USER:-pi}/.Xauthority|g" \
    "${PROJECT_DIR}/${SERVICE_SRC}" > "${SERVICE_DST}"

echo "[1/3] 服务文件已复制到 ${SERVICE_DST}"

# 重载 systemd
systemctl daemon-reload
echo "[2/3] systemd 已重载"

# 启用并启动服务
systemctl enable "${SERVICE_NAME}"
echo "[3/3] 服务已设为开机自启"

echo ""
echo "安装完成！"
echo "启动服务: sudo systemctl start ${SERVICE_NAME}"
echo "查看状态: sudo systemctl status ${SERVICE_NAME}"
echo "查看日志: sudo journalctl -u ${SERVICE_NAME} -f"
echo "========================================"
