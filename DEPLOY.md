# 消防履责工作台 · 部署手册（独立 App）

本服务与 EPM **完全隔离**：独立 Flask 进程（端口 5001）、独立数据库 `fs_standalone`、独立账号体系。
部署在 EPM 同一台服务器（49.232.210.134），**复用 EPM 域名 `ryza.com.cn` 与 EPM 小程序 AppId**，通过 nginx 路径前缀 `/api/fs` 与 EPM 的 `/api` 隔离，互不干扰。

## 一、服务器准备（Ubuntu/CentOS）

```bash
# 安装 Python3 + MySQL
sudo apt update && sudo apt install -y python3 python3-venv python3-pip mysql-server nginx
```

## 二、数据库

```bash
mysql -uroot -p < /opt/fire-safety/backend/schema.sql
# 建库 fs_standalone + 建表（9业务表+4账号表+4增强表）
```

创建专用账号（最小权限）：
```sql
CREATE USER 'fs_user'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON fs_standalone.* TO 'fs_user'@'localhost';
FLUSH PRIVILEGES;
```

## 三、上传与安装后端

```bash
# 上传 backend/ 到服务器（可用 WinSCP / scp）
cd /opt && mkdir -p fire-safety/backend && cd fire-safety/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量（独立小程序正式 AppId / Secret）
cat > .env <<'EOF'
FS_SECRET_KEY=your-strong-random-secret
FS_DB_DSN=mysql+pymysql://fs_user:STRONG_PASSWORD@127.0.0.1:3306/fs_standalone?charset=utf8mb4
WX_APPID=wxe81c9f9794ab7ea8
WX_SECRET=d98c175ca1590881df4147c0ae2de0ff
FS_PORT=5001
EOF

# 导入种子（幂等）
python seed.py
```

## 四、systemd 服务

`/etc/systemd/system/fire-safety.service`:
```ini
[Unit]
Description=Fire Safety Workbench
After=network.target mysql.service

[Service]
WorkingDirectory=/opt/fire-safety/backend
EnvironmentFile=/opt/fire-safety/backend/.env
ExecStart=/opt/fire-safety/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable fire-safety
sudo systemctl start fire-safety
# 健康检查
curl http://127.0.0.1:5001/api/fs/health
```

## 五、Nginx 反向代理 + HTTPS（复用 EPM 域名，路径分发）

EPM 的 nginx 已监听 `443 ssl`、`server_name ryza.com.cn`，并将 `/api/` 转发到 EPM 后端（端口 3000）。
**在 EPM 现有的 `server` 块中追加一条 `location /api/fs/`**，把消防独立后端（端口 5001）挂在同一域名下，路径前缀隔离：

```nginx
# 在 EPM 现有 server (443, server_name ryza.com.cn) 块内追加：
# EPM 本身已存在：location /api/ { proxy_pass http://127.0.0.1:3000; }
# 以及：location / { root /opt/epm/dist; ... }

# ---------- 消防履责独立后端 ----------
location /api/fs/ {
    proxy_pass http://127.0.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 120s;
    # 图片 base64 体积较大，放开 body 限制
    client_max_body_size 20m;
}

# ---------- 消防履责 Web 管理后台（浏览器访问 https://ryza.com.cn/fs-admin/） ----------
location /fs-admin/ {
    alias /opt/fs-admin/;
    index index.html;
    # 单页直接返回 index.html（本后台无前端路由，仅需静态托管）
    try_files $uri $uri/ /fs-admin/index.html;
}
```

> **注意**：`location /api/fs/` 与 `/fs-admin/` 均为独立前缀，nginx 按最长前缀匹配，`/api/fs/` 优先于 `/api/` 命中，与 EPM 共存不冲突。配置后执行 `nginx -t && systemctl reload nginx`。

> **管理后台部署**：将 `fire-safety-app/fs-admin/` 目录上传到服务器 `/opt/fs-admin/`（即 nginx alias 指向的目录），上传命令示例（WinSCP 或 scp）：
> ```bash
> scp -r fire-safety-app/fs-admin root@49.232.210.134:/opt/fs-admin/
> ```
> 之后浏览器访问 `https://ryza.com.cn/fs-admin/`，用 **admin 角色账号**登录即可。

## 六、微信小程序对接（独立小程序正式 AppId）

1. 新小程序 request 合法域名配置 `https://ryza.com.cn`
2. 小程序 `app.js` 已配好：
   - `baseUrl: 'https://ryza.com.cn/api/fs'`
   - `appId: 'wxe81c9f9794ab7ea8'`（独立正式 AppId）
3. 后端 `.env` 已填 `WX_APPID=wxe81c9f9794ab7ea8`、`WX_SECRET=d98c175ca1590881df4147c0ae2de0ff`（新小程序 Secret）
4. 微信开发者工具上传 → 提审 → 发布

## 七、安全要点

- `FS_SECRET_KEY` 务必使用强随机值（`openssl rand -hex 32`）
- MySQL 仅监听 127.0.0.1，不对外开放
- 定期备份 `fs_standalone` 数据库
- 生产开启 `urlCheck:true` 与合法域名校验
- 审计日志在 gunicorn 日志中，可对接 ELK
