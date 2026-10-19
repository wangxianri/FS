# -*- coding: utf-8 -*-
"""
认证路由：注册 / 手机号密码登录 / 微信openid一键登录 / 刷新 / 登出 / 验证码 / 找回密码 / 修改密码 / 资料
"""
import json
import random
import time

from flask import Blueprint, request

import db
from auth import (ok, fail, hash_password, verify_password, check_password_strength,
                  make_access_token, make_refresh_token, auth_required,
                  login_locked, reset_fail, get_fail_count, set_fail_count)
from config import (WX_APPID, WX_SECRET, WX_CODE2SESSION_URL,
                    LOGIN_MAX_FAIL, LOGIN_LOCK_THRESHOLD)

bp = Blueprint("auth", __name__, url_prefix="/api/fs")

_p = lambda: "?" if db.FS_DB_ENGINE != "mysql" else "%s"


# ---------- 图形验证码(简易) ----------
def _gen_code():
    return str(random.randint(1000, 9999))


# ---------- 微信 code 换取 openid ----------
def _wx_code2session(code):
    if not WX_APPID or not WX_SECRET:
        return None, "微信未配置"
    try:
        import requests
        r = requests.get(WX_CODE2SESSION_URL, params={
            "appid": WX_APPID, "secret": WX_SECRET, "js_code": code, "grant_type": "authorization_code"}, timeout=8)
        data = r.json()
    except Exception as e:
        return None, "微信服务请求失败: %s" % e
    if "openid" in data:
        return data, None
    return None, "微信登录失败: %s" % data.get("errmsg", "未知错误")


def _token_payload(user):
    access = make_access_token(user["id"], user["role"], user.get("token_version", 0))
    refresh = make_refresh_token(user["id"], user["role"])
    # 附带角色名与所属单位，保证登录后首页即可展示单位信息
    role_row = db.query_one("SELECT name FROM fs_roles WHERE role_key=%s" % _p(), (user["role"],))
    unit_id = user.get("unit_id") or 0
    unit_name = ""
    if unit_id:
        u = db.query_one("SELECT name FROM fs_units WHERE id=%s" % _p(), (unit_id,))
        if u:
            unit_name = u["name"]
    return {
        "accessToken": access,
        "refreshToken": refresh,
        "expiresIn": 7200,
        "user": {
            "id": user["id"], "phone": user["phone"], "name": user["name"],
            "role": user["role"], "avatar": user["avatar"],
            "roleName": role_row["name"] if role_row else user["role"],
            "unitId": unit_id, "unitName": unit_name,
        },
    }


def _bump_version(user_id):
    db.execute("UPDATE fs_app_users SET token_version=token_version+1 WHERE id=%s" % _p(), (user_id,))


# ---------- 发送验证码 ----------
@bp.route("/sms/send", methods=["POST"])
def send_sms():
    body = request.get_json(silent=True) or {}
    phone = (body.get("phone") or "").strip()
    purpose = body.get("purpose", "register")
    if not phone or len(phone) != 11:
        return fail(400, "手机号格式不正确")
    # 注册校验唯一
    exist = db.query_one("SELECT id FROM fs_app_users WHERE phone=%s" % _p(), (phone,))
    if purpose == "register" and exist:
        return fail(409, "该手机号已注册")
    if purpose in ("forgot", "bind") and not exist:
        return fail(404, "该手机号未注册")
    code = _gen_code()
    db.execute("DELETE FROM fs_sms_codes WHERE phone=%s AND purpose=%s" % (_p(), _p()),
               (phone, purpose))
    db.execute("INSERT INTO fs_sms_codes(phone,code_hash,purpose,expires_at) VALUES(%s,%s,%s,DATE_ADD(NOW(), INTERVAL 10 MINUTE))"
               if db.FS_DB_ENGINE == "mysql" else
               "INSERT INTO fs_sms_codes(phone,code_hash,purpose,expires_at) VALUES(%s,%s,%s,datetime('now','+10 minutes'))",
               (phone, hash_password(code), purpose))
    # 演示环境直接返回验证码
    return ok({"debug": code if not WX_APPID else None}, "验证码已发送")


# ---------- 注册（手机号+密码） ----------
@bp.route("/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}
    phone = (body.get("phone") or "").strip()
    password = body.get("password") or ""
    name = (body.get("name") or "").strip()
    code = body.get("code") or ""
    if not phone or len(phone) != 11:
        return fail(400, "手机号格式不正确")
    if not name:
        name = "用户" + phone[-4:]
    ok_strength, msg = check_password_strength(password)
    if not ok_strength:
        return fail(400, msg)
    exist = db.query_one("SELECT id FROM fs_app_users WHERE phone=%s" % _p(), (phone,))
    if exist:
        return fail(409, "该手机号已注册")
    # 校验验证码
    rec = db.query_one("SELECT * FROM fs_sms_codes WHERE phone=%s AND purpose='register' ORDER BY id DESC LIMIT 1" % _p(), (phone,))
    if not rec or rec.get("used"):
        return fail(400, "请先获取验证码")
    if not verify_password(code, rec["code_hash"]):
        return fail(400, "验证码错误")
    from datetime import datetime
    if db.FS_DB_ENGINE == "mysql":
        now = datetime.now()
        if str(rec["expires_at"]) < str(now):
            return fail(400, "验证码已过期")
    else:
        if rec["expires_at"] and rec["expires_at"] < db._now_str():
            return fail(400, "验证码已过期")
    db.execute("UPDATE fs_sms_codes SET used=1 WHERE id=%s" % _p(), (rec["id"],))
    uid = db.execute(
        "INSERT INTO fs_app_users(phone,password_hash,name,role,last_login_at) VALUES(%s,%s,%s,'grass',NOW())"
        if db.FS_DB_ENGINE == "mysql" else
        "INSERT INTO fs_app_users(phone,password_hash,name,role,last_login_at) VALUES(%s,%s,%s,'grass',datetime('now'))",
        (phone, hash_password(password), name))
    user = db.query_one("SELECT * FROM fs_app_users WHERE id=%s" % _p(), (uid,))
    return ok(_token_payload(user), "注册成功")


# ---------- 手机号+密码 登录 ----------
@bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    phone = (body.get("phone") or "").strip()
    password = body.get("password") or ""
    ip = request.remote_addr or ""
    if login_locked(phone):
        return fail(423, "登录失败次数过多，账号已临时锁定，请 15 分钟后再试")
    user = db.query_one("SELECT * FROM fs_app_users WHERE phone=%s" % _p(), (phone,))
    if not user or not verify_password(password, user["password_hash"]):
        cnt = get_fail_count("phone", phone) + 1
        set_fail_count("phone", phone, cnt)
        if cnt >= LOGIN_LOCK_THRESHOLD:
            set_fail_count("lock", phone, 1)
            return fail(423, "登录失败次数过多，账号已临时锁定，请 15 分钟后再试")
        need_captcha = cnt >= LOGIN_MAX_FAIL
        return fail(401, "手机号或密码错误", {"needCaptcha": need_captcha, "failCount": cnt})
    if user["status"] != 1:
        return fail(403, "账号已被停用，请联系管理员")
    db.execute("UPDATE fs_app_users SET last_login_at=NOW() WHERE id=%s" if db.FS_DB_ENGINE == "mysql"
               else "UPDATE fs_app_users SET last_login_at=datetime('now') WHERE id=%s", (user["id"],))
    reset_fail(phone)
    return ok(_token_payload(user), "登录成功")


# ---------- 微信 openid 一键登录 ----------
@bp.route("/wx/login", methods=["POST"])
def wx_login():
    body = request.get_json(silent=True) or {}
    code = body.get("code") or ""
    if not code:
        return fail(400, "缺少微信登录凭证")
    wxdata, err = _wx_code2session(code)
    if err:
        return fail(502, err)
    openid = wxdata["openid"]
    unionid = wxdata.get("unionid", "")
    bind = db.query_one("SELECT * FROM fs_wechat_bind WHERE openid=%s" % _p(), (openid,))
    if bind:
        user = db.query_one("SELECT * FROM fs_app_users WHERE id=%s" % _p(), (bind["user_id"],))
        if not user:
            return fail(404, "绑定账号不存在")
        if user["status"] != 1:
            return fail(403, "账号已被停用")
        db.execute("UPDATE fs_wechat_bind SET last_login_at=NOW() WHERE openid=%s"
                   if db.FS_DB_ENGINE == "mysql" else
                   "UPDATE fs_wechat_bind SET last_login_at=datetime('now') WHERE openid=%s", (openid,))
        return ok(_token_payload(user), "登录成功")
    # 未绑定：返回 openid 供前端进入绑定流程
    return fail(200, "该微信尚未绑定账号", {"openid": openid, "needBind": True, "unionid": unionid})


# ---------- 微信绑定手机号/账号 ----------
@bp.route("/wx/bind", methods=["POST"])
def wx_bind():
    body = request.get_json(silent=True) or {}
    openid = (body.get("openid") or "").strip()
    phone = (body.get("phone") or "").strip()
    password = body.get("password") or ""       # 绑定已有账号
    code = body.get("code") or ""               # 或用验证码
    mode = body.get("mode", "code")             # code=验证码绑定已注册 / register=新注册并绑定
    if not openid:
        return fail(400, "缺少 openid")
    # 已绑定则拒绝
    if db.query_one("SELECT id FROM fs_wechat_bind WHERE openid=%s" % _p(), (openid,)):
        return fail(409, "该微信已绑定账号")
    if mode == "register":
        # 新注册并绑定：需要手机号+验证码
        name = (body.get("name") or "").strip()
        password = body.get("password") or ""
        rec = db.query_one("SELECT * FROM fs_sms_codes WHERE phone=%s AND purpose='bind' ORDER BY id DESC LIMIT 1" % _p(), (phone,))
        if not rec or rec.get("used") or not verify_password(code, rec["code_hash"]):
            return fail(400, "验证码无效")
        if db.query_one("SELECT id FROM fs_app_users WHERE phone=%s" % _p(), (phone,)):
            return fail(409, "该手机号已注册，请选择绑定已有账号")
        ok_strength, msg = check_password_strength(password)
        if not ok_strength:
            return fail(400, msg)
        db.execute("UPDATE fs_sms_codes SET used=1 WHERE id=%s" % _p(), (rec["id"],))
        uid = db.execute("INSERT INTO fs_app_users(phone,password_hash,name,role) VALUES(%s,%s,%s,'grass')" % (_p(), _p(), _p()),
                         (phone, hash_password(password), name or "用户" + phone[-4:]))
    else:
        # 绑定已有账号：手机号+密码
        user = db.query_one("SELECT * FROM fs_app_users WHERE phone=%s" % _p(), (phone,))
        if not user or not verify_password(password, user["password_hash"]):
            return fail(401, "手机号或密码错误")
        if user["status"] != 1:
            return fail(403, "账号已被停用")
        uid = user["id"]
    db.execute("INSERT INTO fs_wechat_bind(user_id,openid,unionid) VALUES(%s,%s,%s)" % (_p(), _p(), _p()),
               (uid, openid, body.get("unionid", "")))
    user = db.query_one("SELECT * FROM fs_app_users WHERE id=%s" % _p(), (uid,))
    return ok(_token_payload(user), "绑定成功")


# ---------- 刷新令牌 ----------
@bp.route("/refresh", methods=["POST"])
def refresh():
    body = request.get_json(silent=True) or {}
    refresh_token = body.get("refreshToken") or ""
    if not refresh_token:
        return fail(401, "缺少刷新令牌")
    import auth as A
    payload = A.decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return fail(401, "刷新令牌无效")
    user = db.query_one("SELECT * FROM fs_app_users WHERE id=%s" % _p(), (int(payload["sub"]),))
    if not user or user["status"] != 1:
        return fail(401, "账号不可用")
    if user["token_version"] != payload.get("tv", 0):
        return fail(401, "登录状态已变更，请重新登录")
    return ok(_token_payload(user))


# ---------- 登出（使当前所有 token 失效） ----------
@bp.route("/logout", methods=["POST"])
@auth_required
def logout():
    _bump_version(request.user_id)
    return ok(None, "已退出登录")


# ---------- 找回密码 ----------
@bp.route("/forgot", methods=["POST"])
def forgot():
    body = request.get_json(silent=True) or {}
    phone = (body.get("phone") or "").strip()
    code = body.get("code") or ""
    new_password = body.get("newPassword") or ""
    user = db.query_one("SELECT * FROM fs_app_users WHERE phone=%s" % _p(), (phone,))
    if not user:
        return fail(404, "该手机号未注册")
    ok_strength, msg = check_password_strength(new_password)
    if not ok_strength:
        return fail(400, msg)
    rec = db.query_one("SELECT * FROM fs_sms_codes WHERE phone=%s AND purpose='forgot' ORDER BY id DESC LIMIT 1" % _p(), (phone,))
    if not rec or rec.get("used") or not verify_password(code, rec["code_hash"]):
        return fail(400, "验证码无效")
    db.execute("UPDATE fs_sms_codes SET used=1 WHERE id=%s" % _p(), (rec["id"],))
    db.execute("UPDATE fs_app_users SET password_hash=%s, token_version=token_version+1 WHERE id=%s" % (_p(), _p()),
               (hash_password(new_password), user["id"]))
    return ok(None, "密码已重置，请重新登录")


# ---------- 修改密码（登录态） ----------
@bp.route("/change-password", methods=["POST"])
@auth_required
def change_password():
    body = request.get_json(silent=True) or {}
    old_pw = body.get("oldPassword") or ""
    new_pw = body.get("newPassword") or ""
    user = db.query_one("SELECT * FROM fs_app_users WHERE id=%s" % _p(), (request.user_id,))
    if not verify_password(old_pw, user["password_hash"]):
        return fail(401, "原密码错误")
    ok_strength, msg = check_password_strength(new_pw)
    if not ok_strength:
        return fail(400, msg)
    db.execute("UPDATE fs_app_users SET password_hash=%s, token_version=token_version+1 WHERE id=%s" % (_p(), _p()),
               (hash_password(new_pw), user["id"]))
    return ok(None, "密码修改成功，请重新登录")


# ---------- 当前用户资料 ----------
@bp.route("/me", methods=["GET"])
@auth_required
def me():
    user = request.user
    role_row = db.query_one("SELECT * FROM fs_roles WHERE role_key=%s" % _p(), (user["role"],))
    modules = json.loads(role_row["modules"]) if role_row and role_row.get("modules") else []
    unit_id = user.get("unit_id") or 0
    unit_name = ""
    if unit_id:
        u = db.query_one("SELECT name FROM fs_units WHERE id=%s" % _p(), (unit_id,))
        if u:
            unit_name = u["name"]
    return ok({
        "id": user["id"], "phone": user["phone"], "name": user["name"],
        "role": user["role"], "roleName": role_row["name"] if role_row else user["role"],
        "avatar": user["avatar"], "modules": modules,
        "unitId": unit_id, "unitName": unit_name,
        "hasWechat": bool(db.query_one("SELECT id FROM fs_wechat_bind WHERE user_id=%s" % _p(), (user["id"],))),
    })
