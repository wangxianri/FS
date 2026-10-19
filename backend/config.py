# -*- coding: utf-8 -*-
"""
消防履责助手 独立 App · 配置模块
独立于 EPM，零侵入
"""
import os

# ---------- 基础 ----------
FS_APP_NAME = "消防履责助手"
FS_VERSION = "2.0.0"

# ---------- JWT ----------
FS_SECRET_KEY = os.getenv("FS_SECRET_KEY", "change-me-fs-standalone-secret-2026")
JWT_ALGO = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("FS_ACCESS_MINUTES", "120"))     # 2h
REFRESH_TOKEN_DAYS = int(os.getenv("FS_REFRESH_DAYS", "7"))            # 7天

# ---------- 数据库 ----------
# MySQL DSN: mysql+pymysql://user:pass@127.0.0.1:3306/fs_standalone?charset=utf8mb4
# 缺省回退到本地 SQLite（开发/演示用）
FS_DB_DSN = os.getenv("FS_DB_DSN", "")
_DEFAULT_SQLITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fs_standalone.db")
FS_DB_ENGINE = "mysql" if FS_DB_DSN.startswith("mysql") else "sqlite"

# ---------- 微信小程序 ----------
# 独立小程序正式 AppId/Secret（与 EPM 小程序解耦，openid 独立体系）
WX_APPID = os.getenv("WX_APPID", "wxe81c9f9794ab7ea8")
WX_SECRET = os.getenv("WX_SECRET", "d98c175ca1590881df4147c0ae2de0ff")
WX_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"

# ---------- 密码 ----------
PBKDF2_ITERATIONS = 600000
WEAK_PASSWORDS = {"12345678", "123456789", "1234567890", "11111111", "00000000",
                  "aaaaaaaa", "password", "qwertyui", "admin123"}

# ---------- 防爆破 ----------
LOGIN_MAX_FAIL = 5          # 5 次失败需图形验证码
LOGIN_LOCK_THRESHOLD = 15   # 15 次锁定
LOGIN_LOCK_SECONDS = 900    # 锁定 15 分钟
