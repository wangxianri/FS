# -*- coding: utf-8 -*-
"""
消防履责助手 独立 App · 后端入口
独立于 EPM，独立端口，独立数据库，独立账号体系
启动: python app.py  (默认 0.0.0.0:5001)
"""
import hashlib
import logging
from datetime import date, datetime

from flask import Flask, request
from flask.json.provider import DefaultJSONProvider

import db
from auth import ok, auth_required
from config import FS_APP_NAME, FS_VERSION

# ---------- 应用 ----------
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ---------- 统一 JSON 日期出口 ----------
class FSJSONProvider(DefaultJSONProvider):
    """统一日期出口：DATE -> YYYY-MM-DD，DATETIME -> YYYY-MM-DD HH:MM:SS。

    默认的 DefaultJSONProvider 会用 http_date() 输出 RFC1123（如
    'Wed, 16 Sep 2026 09:20:41 GMT'），前端按 YYYY-MM-DD 解析/比较会全部失效。
    """

    def __init__(self, app):
        super().__init__(app)
        # Flask >= 2.3 的 DefaultJSONProvider 不再读取 JSON_AS_ASCII，此处显式继承该配置，
        # 使中文按 UTF-8 原样输出（与 app.config["JSON_AS_ASCII"] = False 的既定意图一致）。
        self.ensure_ascii = bool(app.config.get("JSON_AS_ASCII", True))

    @staticmethod
    def default(o):
        if isinstance(o, datetime):   # 必须先于 date 判断（datetime 是 date 的子类）
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, date):
            return o.strftime("%Y-%m-%d")
        return DefaultJSONProvider.default(o)


# 实例化（基类 __init__ 会读取 JSON_AS_ASCII，保证中文不被转义）
app.json = FSJSONProvider(app)


# ---------- 注册蓝图 ----------
def register_blueprints():
    from auth_routes import bp as auth_bp
    from biz_routes import bp as biz_bp
    from admin_routes import bp as admin_bp
    from enhance_routes import bp as enhance_bp
    from manage_routes import bp as manage_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(biz_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(enhance_bp)
    app.register_blueprint(manage_bp)


register_blueprints()


# ---------- 健康检查 ----------
@app.route("/api/fs/health", methods=["GET"])
def health():
    db_ok = True
    try:
        db.query_one("SELECT 1 AS x")
    except Exception as e:
        db_ok = False
        logging.error("db health fail: %s", e)
    return ok({
        "app": FS_APP_NAME, "version": FS_VERSION,
        "engine": db.FS_DB_ENGINE, "db": "ok" if db_ok else "fail",
        "ts": __import__("time").time(),
    })


@app.route("/api/fs/ping", methods=["GET"])
def ping():
    return ok(None, "pong")


# ---------- 微信服务器配置验证（Token 校验 / 消息推送） ----------
WX_VERIFY_TOKEN = "6kZZG6W1xU8NVvpN"


@app.route("/api/fs/wx/verify", methods=["GET"])
def wx_verify():
    signature = request.args.get("signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")
    echostr = request.args.get("echostr", "")
    if not (signature and timestamp and nonce and echostr):
        return "missing params", 400
    tmp = sorted([WX_VERIFY_TOKEN, timestamp, nonce])
    calc = hashlib.sha1("".join(tmp).encode("utf-8")).hexdigest()
    if calc == signature:
        return echostr
    return "verify fail", 403


# ---------- 简单审计日志（写日志文件） ----------
@app.before_request
def audit_log():
    if request.path.startswith("/api/fs"):
        uid = getattr(request, "user_id", None)
        logging.info("[fs] %s %s user=%s", request.method, request.path, uid)


if __name__ == "__main__":
    # 初始化 schema（SQLite 自动建表；MySQL 需先导入 schema.sql）
    db.init_schema()
    # 种子（幂等）
    try:
        import seed
        seed.seed()
    except Exception as e:
        logging.warning("seed skipped: %s", e)
    port = int(__import__("os").environ.get("FS_PORT", "5001"))
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
