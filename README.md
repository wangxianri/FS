# 消防履责工作台 独立 App（微信小程序）

依据《消防履责工作台独立App开发需求规格书 V2.0》开发，**完全独立于 EPM**：独立后端、独立数据库、独立账号体系（JWT + 手机号/微信 openid 双通道）。页面设计借鉴 EPM 消防履责模块。提供**微信小程序前端** + **Web 管理后台**（`/fs-admin/`，复用同一套 `/api/fs` 接口）。

## 目录结构

```
fire-safety-app/
├── backend/                 # 独立后端 (Flask, 端口 5001)
│   ├── app.py               # 入口
│   ├── config.py            # 配置（JWT/DB/微信）
│   ├── db.py                # 数据库访问（MySQL/SQLite）
│   ├── auth.py              # JWT + 密码哈希 + 角色装饰器 + 防爆破
│   ├── auth_routes.py       # 认证接口（12个）
│   ├── biz_routes.py        # 业务接口（20个）
│   ├── admin_routes.py      # 账号管理接口
│   ├── enhance_routes.py    # 增强接口（P1/P2）
│   ├── seed_data.py         # 种子常量（角色/模板/量化/操作卡等）
│   ├── seed.py              # 种子写入脚本
│   ├── schema.sql           # 数据库表结构
│   ├── requirements.txt
│   └── .env.example
└── miniprogram/             # 独立微信小程序
    ├── app.js / app.json / app.wxss
    ├── custom-tab-bar/      # 自定义底部导航
    ├── utils/
    │   ├── api.js           # Bearer JWT + 401自动续期 + 离线拦截
    │   ├── auth.js          # 登录/注册/微信一键登录
    │   ├── store.js         # 本地存储
    │   ├── format.js        # 格式化
    │   └── i18n.js          # 三语翻译 (zh-CN/en-US/zh-TW)
    └── pages/
        ├── auth/            # login/register/wx-bind/forgot
        ├── fire/            # 业务+增强页面
        ├── mine/            # 我的
        └── admin/           # 账号管理
└── fs-admin/                # Web 管理后台（浏览器访问 https://ryza.com.cn/fs-admin/）
    └── index.html           # 登录 + 数据总览 + 账号/隐患/任务管理（单页）
```

## 后端部署

```bash
cd backend
pip install -r requirements.txt

# 1. 配置 .env（密钥、数据库、微信）
cp .env.example .env

# 2. MySQL 建库（生产）
mysql -uroot -p < schema.sql

# 3. 导入种子（幂等）
python seed.py

# 4. 启动（开发）
python app.py               # 0.0.0.0:5001

# 生产（gunicorn）
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

**开发/演示模式**：若 `FS_DB_DSN` 留空，自动使用本地 SQLite（`fs_standalone.db`），`python app.py` 会自动建表+导种子，开箱即用。

## 小程序配置

1. 用微信开发者工具导入 `miniprogram/` 目录
2. `app.js` 已配置 `baseUrl: 'https://ryza.com.cn/api/fs'`（**复用 EPM 域名**，路径前缀 `/api/fs` 与 EPM 的 `/api` 隔离）
3. `app.js` 已配置 `appId: 'wxe81c9f9794ab7ea8'`（**独立小程序正式 AppId**，openid 与 EPM 解耦）
4. 在微信公众平台（新小程序）配置 request 合法域名（`https://ryza.com.cn`）
5. 后端 `.env` 中 `WX_APPID` 填 `wxe81c9f9794ab7ea8`、`WX_SECRET` 填新小程序 Secret，以启用微信一键登录

> 开发期可在 `project.config.json` 中设置 `urlCheck:false` 跳过域名校验。

## 认证体系（V2.0）

- **JWT 双令牌**：access(2h) + refresh(7d)，`token_version` 机制支持停用/改密/登出即时失效
- **双通道登录**：手机号+密码 / 微信 openid 一键登录（未绑定进入绑定页）
- **防爆破**：5次失败需图形验证码、15次锁定15分钟
- **角色权限矩阵**：grass(基层)/mid(中层)/top(领导)/accept(验收)/admin(管理员)，前端菜单与后端接口双重校验
- **离线模式**：网络异常自动入队，恢复后 `/offline/sync` 幂等同步

## 关键 API 一览

| 分类 | 接口 |
|------|------|
| 认证 | `/register` `/login` `/wx/login` `/wx/bind` `/refresh` `/logout` `/forgot` `/change-password` `/me` `/sms/send` |
| 业务 | `/tasks` `/tasks/<id>/inspect` `/hazards` `/hazards/<id>/rectify|recheck|close|reopen` `/ledger` `/acceptance` `/check-items` `/reference` `/quant` `/photos` `/home` `/hazards/board` |
| 增强 | `/spot/check` `/supervise` `/quiz/submit` `/emg/cards` `/equip/guides` `/offline/sync` |
| 管理 | `/admin/users` |
| 健康 | `/health` `/ping` |

## Web 管理后台（/fs-admin/）

浏览器访问 `https://ryza.com.cn/fs-admin/`，用 **admin 角色**账号登录（复用 `/api/fs/login`，令牌存 localStorage）。功能：

- **数据总览**：首页统计 + 隐患看板（数量/状态/等级/超期/区域聚合）
- **账号管理**：列表/搜索/新增/停用启用/改角色/重置密码/删除
- **隐患管理**：按状态/等级筛选，直接闭环 / 重开
- **任务管理**：按状态/周期筛选，查看得分与应做日期

> 管理后台仅 `admin` 角色可登录（登录后校验 `role==='admin'`，否则拒绝）。将 `fs-admin/` 上传到服务器 `/opt/fs-admin/` 并由 nginx `/fs-admin/` 静态托管（详见 `DEPLOY.md`）。
