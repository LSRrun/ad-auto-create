#!/bin/bash
set -e

PROJECT_DIR="/root/projects/ad-auto-create"
CONDA_ENV="adcreate"
PYTHON_BIN="/root/miniconda3/envs/${CONDA_ENV}/bin/python"

echo "========================================="
echo "  广告自动生成器 - 一键部署脚本"
echo "========================================="

cd "$PROJECT_DIR"

# 1. 拉取最新代码
echo ""
echo "[1/6] 拉取最新代码..."
git pull

# 2. 安装后端依赖
echo ""
echo "[2/6] 安装后端依赖..."
$PYTHON_BIN -m pip install -r backend/requirements.txt -q

# 3. 构建前端
echo ""
echo "[3/6] 构建前端..."
cd "$PROJECT_DIR/frontend"
npm install --production=false
npm run build
echo "前端构建完成，输出目录: frontend/dist/"

# 4. 配置 Nginx
echo ""
echo "[4/6] 配置 Nginx..."
cp "$PROJECT_DIR/deploy/nginx.conf" /etc/nginx/conf.d/ad-auto-create.conf

# 检查 Nginx 是否安装
if ! command -v nginx &> /dev/null; then
    echo "Nginx 未安装，正在安装..."
    yum install -y nginx
fi

# 测试 Nginx 配置
nginx -t

# 5. 配置 systemd 服务
echo ""
echo "[5/6] 配置后端服务..."
cp "$PROJECT_DIR/deploy/ad-api.service" /etc/systemd/system/ad-api.service
systemctl daemon-reload
systemctl enable ad-api
systemctl restart ad-api

# 6. 启动 Nginx
echo ""
echo "[6/6] 启动 Nginx..."
systemctl enable nginx
systemctl restart nginx

# 开放 80 端口（firewalld）
if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --reload
fi

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "  访问地址: http://101.200.187.130"
echo ""
echo "  常用命令:"
echo "    查看后端状态:  systemctl status ad-api"
echo "    查看后端日志:  journalctl -u ad-api -f"
echo "    重启后端:      systemctl restart ad-api"
echo "    重启 Nginx:    systemctl restart nginx"
echo "    重新部署:      bash deploy/deploy.sh"
echo ""
echo "========================================="
