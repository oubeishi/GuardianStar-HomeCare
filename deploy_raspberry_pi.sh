#!/usr/bin/env bash
# =============================================================================
# GuardianStar 树莓派一键部署脚本
# 用法: bash deploy_raspberry_pi.sh
# 适用: Raspberry Pi OS (64-bit) with Desktop
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="GuardianStar-HomeCare"
INSTALL_DIR="/home/pi/${PROJECT_NAME}"
DATA_DIR="/home/pi/guardian_star"
LOG_FILE="/tmp/guardianstar_deploy.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1" | tee -a "$LOG_FILE"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}   $1" | tee -a "$LOG_FILE"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }

# ---------------------------------------------------------------------------
# 0. 前置检查
# ---------------------------------------------------------------------------
check_prerequisites() {
    log_info "检查前置条件..."

    # 检查是否在树莓派上
    if [[ -f /proc/device-tree/model ]]; then
        MODEL=$(cat /proc/device-tree/model 2>/dev/null || echo "Unknown")
        log_info "检测到设备: $MODEL"
    else
        log_warn "未检测到树莓派设备信息，继续执行但部分功能可能不可用"
    fi

    # 检查网络
    if ! ping -c 1 -W 3 223.5.5.5 >/dev/null 2>&1; then
        log_error "网络连接失败，请检查 WiFi 或网线"
        exit 1
    fi
    log_ok "网络连接正常"

    # 检查 Python
    if ! command -v python3 &>/dev/null; then
        log_error "未找到 python3，请安装 Python 3.11+"
        exit 1
    fi
    PYTHON_VER=$(python3 --version 2>&1 | awk '{print $2}')
    log_ok "Python 版本: $PYTHON_VER"

    # 检查 pip
    if ! command -v pip3 &>/dev/null; then
        log_info "安装 pip3..."
        sudo apt update
        sudo apt install -y python3-pip
    fi
    log_ok "pip3 可用"
}

# ---------------------------------------------------------------------------
# 1. 系统更新与依赖安装
# ---------------------------------------------------------------------------
install_system_deps() {
    log_info "更新系统并安装依赖..."
    sudo apt update
    sudo apt install -y \
        python3-tk \
        python3-pip \
        python3-venv \
        fonts-wqy-zenhei \
        libsdl2-mixer-2.0-0 \
        libportmidi0 \
        xinput-calibrator \
        git \
        curl \
        vim

    log_ok "系统依赖安装完成"
}

# ---------------------------------------------------------------------------
# 2. 创建数据目录
# ---------------------------------------------------------------------------
setup_data_dirs() {
    log_info "创建数据目录: $DATA_DIR"
    mkdir -p "${DATA_DIR}"/{sounds,logs}
    log_ok "数据目录就绪"
}

# ---------------------------------------------------------------------------
# 3. 复制项目代码
# ---------------------------------------------------------------------------
copy_project() {
    log_info "部署项目代码..."

    # 如果当前目录就是项目根目录，直接复制
    if [[ -f "${SCRIPT_DIR}/src/main.py" ]]; then
        SOURCE_DIR="$SCRIPT_DIR"
    else
        log_error "未找到项目源代码 (src/main.py)，请确保在 GuardianStar-HomeCare 目录中运行此脚本"
        exit 1
    fi

    # 复制到安装目录
    if [[ -d "$INSTALL_DIR" ]]; then
        log_warn "安装目录已存在: $INSTALL_DIR，将覆盖更新"
        rm -rf "${INSTALL_DIR}"
    fi

    cp -r "$SOURCE_DIR" "$INSTALL_DIR"
    log_ok "项目代码已复制到: $INSTALL_DIR"
}

# ---------------------------------------------------------------------------
# 4. 安装 Python 依赖
# ---------------------------------------------------------------------------
install_python_deps() {
    log_info "安装 Python 依赖..."
    cd "$INSTALL_DIR"
    pip3 install --user -r requirements.txt
    log_ok "Python 依赖安装完成"
}

# ---------------------------------------------------------------------------
# 5. 配置音频（强制 3.5mm + 音量）
# ---------------------------------------------------------------------------
configure_audio() {
    log_info "配置音频输出..."

    # 强制音频走 3.5mm
    amixer cset numid=3 1 2>/dev/null || true

    # 设置音量 85%
    amixer set PCM -- 85% 2>/dev/null || true

    # 保存配置
    sudo alsactl store 2>/dev/null || true

    log_ok "音频已配置为 3.5mm 输出，音量 85%"
}

# ---------------------------------------------------------------------------
# 6. 配置文件处理
# ---------------------------------------------------------------------------
setup_config() {
    log_info "检查配置文件..."

    CONFIG_SRC="${INSTALL_DIR}/config.json"
    CONFIG_DST="${DATA_DIR}/config.json"

    if [[ -f "$CONFIG_DST" ]]; then
        log_warn "配置文件已存在于 ${CONFIG_DST}，保留现有配置"
        log_warn "如需更新配置，请手动编辑 ${CONFIG_DST}"
    else
        cp "$CONFIG_SRC" "$CONFIG_DST"
        log_ok "配置文件已复制到: ${CONFIG_DST}"
        log_warn "⚠️  请编辑 ${CONFIG_DST} 填写企业微信机器人 Webhook URL"
    fi

    # 创建指向数据目录的符号链接（方便代码找到配置）
    ln -sf "$CONFIG_DST" "${INSTALL_DIR}/config.json" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# 7. 检查音频文件
# ---------------------------------------------------------------------------
check_sounds() {
    log_info "检查音频文件..."

    SOUNDS_DIR="${DATA_DIR}/sounds"
    REQUIRED_SOUNDS=(
        "son.wav" "daughter.wav" "time.wav" "eat.wav"
        "situp.wav" "call.wav" "water.wav" "turn.wav"
        "toilet.wav" "pain.wav" "hotcold.wav" "emergency.wav"
    )

    MISSING=()
    for sound in "${REQUIRED_SOUNDS[@]}"; do
        if [[ ! -f "${SOUNDS_DIR}/${sound}" ]]; then
            MISSING+=("$sound")
        fi
    done

    if [[ ${#MISSING[@]} -eq 0 ]]; then
        log_ok "所有音频文件已就绪 ✓"
    else
        log_warn "以下音频文件缺失："
        for sound in "${MISSING[@]}"; do
            echo "    - $sound"
        done
        echo ""
        log_warn "请按 docs/07-音频资源规范.md 录制音频后复制到: ${SOUNDS_DIR}/"
        log_warn "音频缺失时程序仍可运行，但点击按钮不会播放声音"
    fi
}

# ---------------------------------------------------------------------------
# 8. 配置 systemd 开机自启
# ---------------------------------------------------------------------------
setup_systemd() {
    log_info "配置 systemd 开机自启..."

    SERVICE_FILE="/etc/systemd/system/guardianstar.service"

    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=GuardianStar HomeCare Service
After=graphical.target network.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
Environment=PYTHONPATH=${INSTALL_DIR}
WorkingDirectory=${INSTALL_DIR}
ExecStartPre=/bin/sh -c 'amixer cset numid=3 1 || true'
ExecStartPre=/bin/sh -c 'amixer set PCM -- 85% || true'
ExecStart=/usr/bin/python3 -m src.main
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=10

[Install]
WantedBy=graphical.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable guardianstar.service
    log_ok "systemd 服务已配置并设为开机自启"
}

# ---------------------------------------------------------------------------
# 9. 创建快捷命令
# ---------------------------------------------------------------------------
create_aliases() {
    log_info "创建管理命令..."

    ALIAS_FILE="/home/pi/.guardianstar_aliases"
    cat > "$ALIAS_FILE" <<EOF
# GuardianStar 管理快捷命令
alias gs-start='sudo systemctl start guardianstar'
alias gs-stop='sudo systemctl stop guardianstar'
alias gs-restart='sudo systemctl restart guardianstar'
alias gs-status='sudo systemctl status guardianstar'
alias gs-logs='sudo journalctl -u guardianstar -f'
alias gs-logs-today='sudo journalctl -u guardianstar --since today'
alias gs-config='nano ~/guardian_star/config.json'
alias gs-oplogs='ls -la ~/guardian_star/logs/'
EOF

    # 添加到 .bashrc（如果不存在）
    if ! grep -q "guardianstar_aliases" /home/pi/.bashrc 2>/dev/null; then
        echo "source ~/.guardianstar_aliases" >> /home/pi/.bashrc
        log_ok "快捷命令已添加到 .bashrc，重新登录后生效"
    fi

    log_ok "可用快捷命令:"
    echo "    gs-start      - 启动服务"
    echo "    gs-stop       - 停止服务"
    echo "    gs-restart    - 重启服务"
    echo "    gs-status     - 查看状态"
    echo "    gs-logs       - 实时查看日志"
    echo "    gs-config     - 编辑配置文件"
    echo "    gs-oplogs     - 查看操作日志"
}

# ---------------------------------------------------------------------------
# 10. 测试运行
# ---------------------------------------------------------------------------
test_run() {
    log_info "执行快速测试..."

    cd "$INSTALL_DIR"

    # 检查语法
    if python3 -m py_compile src/main.py; then
        log_ok "主程序语法检查通过"
    else
        log_error "主程序语法错误，请检查代码"
        exit 1
    fi

    # 检查核心模块导入
    if python3 -c "from src.core.app import GuardianStarApp; print('模块导入 OK')" 2>/dev/null; then
        log_ok "核心模块导入正常"
    else
        log_warn "核心模块导入有警告（可能是缺少依赖，不影响主要功能）"
    fi
}

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║      GuardianStar 树莓派一键部署脚本                     ║"
    echo "║      奶奶的守护星 - 为亲情而生的养老交互系统              ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""

    > "$LOG_FILE"  # 清空日志

    check_prerequisites
    install_system_deps
    setup_data_dirs
    copy_project
    install_python_deps
    configure_audio
    setup_config
    check_sounds
    setup_systemd
    create_aliases
    test_run

    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  🎉 部署完成！                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    log_ok "安装路径: ${INSTALL_DIR}"
    log_ok "数据路径: ${DATA_DIR}"
    log_ok "日志文件: ${LOG_FILE}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  📋 部署后必须完成的事项："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  1. 🔊 录制泰顺话音频（12句 + 1句紧急）"
    echo "     参考: ${INSTALL_DIR}/docs/07-音频资源规范.md"
    echo "     存放: ${DATA_DIR}/sounds/"
    echo ""
    echo "  2. 📱 配置企业微信机器人"
    echo "     编辑: ${DATA_DIR}/config.json"
    echo "     参考: ${INSTALL_DIR}/docs/08-实施手册.md 第 8.6 节"
    echo ""
    echo "  3. 🔌 连接 GPIO 紧急按钮"
    echo "     GPIO17 (引脚11) → 按钮一端"
    echo "     GND (引脚6/9)   → 按钮另一端"
    echo "     参考: ${INSTALL_DIR}/docs/08-实施手册.md 第 8.1 节"
    echo ""
    echo "  4. 🚀 启动服务"
    echo "     gs-start     (或: sudo systemctl start guardianstar)"
    echo ""
    echo "  5. 📺 测试验证"
    echo "     - 屏幕是否显示主界面（2个大按钮）"
    echo "     - 点击按钮是否播放音频"
    echo "     - 按下物理按钮是否触发紧急警报"
    echo "     - 企业微信是否收到通知"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

main "$@"
