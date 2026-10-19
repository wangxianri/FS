#!/usr/bin/env bash
# ============================================================
# 消防履责工作台 · 服务端切换到独立小程序正式 AppId
# 在服务器上执行（生产环境 systemd 通过 EnvironmentFile 读取 .env）
# 用法: bash switch_appid.sh
# ============================================================
set -e

ENV_FILE="/opt/fire-safety/backend/.env"
NEW_APPID="wxe81c9f9794ab7ea8"
NEW_SECRET="d98c175ca1590881df4147c0ae2de0ff"

# 备份
if [ -f "$ENV_FILE" ]; then
  cp "$ENV_FILE" "$ENV_FILE.bak.$(date +%Y%m%d_%H%M%S)"
  echo "[OK] 已备份 .env -> $ENV_FILE.bak.*"
else
  echo "[WARN] 未找到 $ENV_FILE，将新建"
  mkdir -p "$(dirname "$ENV_FILE")"
  touch "$ENV_FILE"
fi

update_or_append() {
  local key="$1"
  local val="$2"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
    echo "[OK] 已更新 ${key}"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
    echo "[OK] 已追加 ${key}"
  fi
}

update_or_append "WX_APPID" "$NEW_APPID"
update_or_append "WX_SECRET" "$NEW_SECRET"

echo "--- 当前 .env 中的微信配置 ---"
grep -E "^WX_APPID=|^WX_SECRET=" "$ENV_FILE" || true

# 重启服务（支持两种常见部署方式）
if systemctl list-units --type=service 2>/dev/null | grep -q "fire-safety.service"; then
  echo "[OK] 重启 systemd 服务 fire-safety"
  sudo systemctl daemon-reload
  sudo systemctl restart fire-safety
elif command -v docker &>/dev/null && docker ps 2>/dev/null | grep -qi fire; then
  echo "[OK] Docker 部署，重建容器"
  sudo docker compose up -d --force-recreate
else
  echo "[WARN] 未识别部署方式，请手动重启 fire-safety 服务"
fi

sleep 3

echo "--- 健康检查 ---"
curl -s https://ryza.com.cn/api/fs/health || curl -s http://127.0.0.1:5001/api/fs/health || echo "[FAIL] 健康检查未通过，请检查服务"

echo ""
echo "=== 完成 ==="
echo "如果健康检查通过，说明后端已切换到新 AppId。"
echo "请在微信公众平台（新小程序后台）配置 request 合法域名: https://ryza.com.cn"
