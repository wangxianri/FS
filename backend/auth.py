# -*- coding: utf-8 -*-
"""
鉴权模块：JWT 签发/校验、密码哈希、角色装饰器、登录防爆破
独立于 EPM
"""
import hashlib
import hmac
import time
import re
import functools

import jwt
from flask import request, jsonify

import db
from config import (FS_SECRET_KEY, JWT_ALGO, ACCESS_TOKEN_MINUTES, REFRESH_TOKEN_DAYS,
                    PBKDF2_ITERATIONS, WEAK_PASSWORDS, LOGIN_MAX_FAIL,
                    LOGIN_LOCK_THRESHOLD, LOGIN_LOCK_SECONDS)

# ---------- 密码哈希（pbkdf2 sha256 + 随机盐） ----------
def hash_password(password: str) -> str:
    salt = hashlib.sha256(str(time.time()).encode() + password.encode()).hexdigest()[:16]
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, hexdigest = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iters))
        return hmac.compare_digest(dk.hex(), hexdigest)
    except Exception:
        return False


def check_password_strength(pw: str) -> (bool, str):
    if len(pw) < 8:
        return False, "密码长度至少 8 位"
    if not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        return False, "密码需同时包含字母和数字"
    if pw.lower() in WEAK_PASSWORDS:
        return False, "密码过于简单，请更换"
    if re.fullmatch(r"(\d)\1*", pw):
        return False, "密码过于简单，请更换"
    return True, ""


# ---------- JWT ----------
def make_access_token(user_id, role, tv=0):
    payload = {"sub": str(user_id), "role": role, "type": "access", "tv": int(tv or 0),
               "exp": int(time.time()) + ACCESS_TOKEN_MINUTES * 60}
    return jwt.encode(payload, FS_SECRET_KEY, algorithm=JWT_ALGO)


def make_refresh_token(user_id, role):
    payload = {"sub": str(user_id), "role": role, "type": "refresh",
               "exp": int(time.time()) + REFRESH_TOKEN_DAYS * 86400}
    return jwt.encode(payload, FS_SECRET_KEY, algorithm=JWT_ALGO)


def decode_token(token):
    try:
        return jwt.decode(token, FS_SECRET_KEY, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None


# ---------- 用户会话校验 ----------
def load_user_by_id(user_id):
    return db.query_one("SELECT * FROM fs_app_users WHERE id=%s" % ("?" if db.FS_DB_ENGINE != "mysql" else "%s"), (user_id,))


def user_valid(payload):
    """校验 access token + token_version + 用户启用态"""
    if not payload or payload.get("type") != "access":
        return None
    try:
        uid = int(payload.get("sub"))
    except Exception:
        return None
    user = load_user_by_id(uid)
    if not user or user["status"] != 1:
        return None
    if user["token_version"] != payload.get("tv", 0):
        return None
    return user


# ---------- 登录防爆破 ----------
def _fail_key(kind, key):
    return f"fs_login_fail_{kind}_{key}"


def get_fail_count(kind, key):
    row = db.query_one(
        "SELECT meta_value FROM fs_meta WHERE meta_key=%s" % ("?" if db.FS_DB_ENGINE != "mysql" else "%s"),
        (_fail_key(kind, key),))
    if not row:
        return 0
    try:
        v = int(row["meta_value"])
    except Exception:
        return 0
    return v


def set_fail_count(kind, key, count):
    meta_key = _fail_key(kind, key)
    row = db.query_one(
        "SELECT id FROM fs_meta WHERE meta_key=%s" % ("?" if db.FS_DB_ENGINE != "mysql" else "%s"),
        (meta_key,))
    if row:
        db.execute("UPDATE fs_meta SET meta_value=%s WHERE meta_key=%s" % (
            ("%s" if db.FS_DB_ENGINE != "mysql" else "%s"),
            ("%s" if db.FS_DB_ENGINE != "mysql" else "%s")), (str(count), meta_key))
    else:
        db.execute("INSERT INTO fs_meta(meta_key,meta_value) VALUES(%s,%s)" % (
            ("?" if db.FS_DB_ENGINE != "mysql" else "%s"),
            ("?" if db.FS_DB_ENGINE != "mysql" else "%s")), (meta_key, str(count)))


def login_locked(phone):
    return get_fail_count("lock", phone) > 0


def reset_fail(phone):
    for kind in ("phone", "ip", "lock"):
        set_fail_count(kind, phone, 0)


# ---------- 响应工具 ----------
def ok(data=None, message="ok"):
    return jsonify({"code": 200, "message": message, "data": data})


def fail(code, message, data=None):
    return jsonify({"code": code, "message": message, "data": data}), code


# ---------- 装饰器 ----------
def auth_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "").strip() if auth.startswith("Bearer") else ""
        if not token:
            return fail(401, "未登录或登录已过期")
        payload = decode_token(token)
        user = user_valid(payload)
        if not user:
            return fail(401, "登录已失效，请重新登录")
        request.user = user
        request.user_id = user["id"]
        return fn(*args, **kwargs)
    return wrapper


def require_role(*roles):
    def decorator(fn):
        @functools.wraps(fn)
        @auth_required
        def wrapper(*args, **kwargs):
            user = request.user
            if user["role"] not in roles:
                return fail(403, "无权限访问该功能")
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# admin 角色判断
def is_admin(user):
    return user["role"] == "admin"


# ---------- 三级单位数据权限（树形继承：本级 + 所有下级单位） ----------
def collect_subtree_unit_ids(root_id):
    """返回 root_id 及其所有下级单位的 id 列表（BFS 向下扩展，防脏数据死循环）。"""
    root_id = int(root_id or 0)
    if root_id <= 0:
        return []
    ids = [root_id]
    seen = {root_id}
    frontier = [root_id]
    while frontier:
        marks = db._ph(len(frontier))
        rows = db.query(
            "SELECT id FROM fs_units WHERE parent_id IN (%s)" % marks, tuple(frontier))
        children = [r["id"] for r in rows if r["id"] not in seen]
        if not children:
            break
        seen.update(children)
        ids.extend(children)
        frontier = children
    return ids


def get_visible_unit_ids(user):
    """返回用户可见的单位 id 列表（含本级及所有下级单位）。
    - 系统管理员（admin）：返回 None，表示不限制（可看全部）
    - 其他角色：根据 user.unit_id 递归收集本级 + 所有下级单位
    - 未分配单位的非 admin：返回空列表（看不到任何单位数据）
    """
    if user["role"] == "admin":
        return None
    uid = user.get("unit_id") or 0
    if uid <= 0:
        return []
    return collect_subtree_unit_ids(uid)


def scope_unit_filter(user, alias="unit_id"):
    """根据用户可见单位范围返回 SQL 过滤片段 (sql_snippet, params)。
    - admin：返回 ("", [])，不附加过滤
    - 非 admin 未分配单位：返回 (" AND 1=0", [])，强制空结果
    - 非 admin 正常：返回 (" AND {alias} IN (%s,%s,...)", [ids...])
    """
    ids = get_visible_unit_ids(user)
    if ids is None:
        return "", []
    if not ids:
        return " AND 1=0", []
    marks = db._ph(len(ids))
    return " AND %s IN (%s)" % (alias, marks), list(ids)
