# -*- coding: utf-8 -*-
"""
管理路由：账号管理（仅 admin）
列表 / 新增 / 停用启用 / 重置密码 / 改角色 / 删除
"""
from flask import Blueprint, request

import db
from auth import ok, fail, require_role, hash_password, check_password_strength

bp = Blueprint("admin", __name__, url_prefix="/api/fs/admin")
_p = lambda: "?" if db.FS_DB_ENGINE != "mysql" else "%s"


@bp.route("/users", methods=["GET"])
@require_role("admin")
def list_users():
    q = request.args.get("q", "").strip()
    sql = ("SELECT u.id,u.phone,u.name,u.role,u.status,u.unit_id,u.last_login_at,u.created_at,"
           "un.name AS unit_name "
           "FROM fs_app_users u LEFT JOIN fs_units un ON u.unit_id=un.id WHERE 1=1")
    params = []
    if q:
        sql += " AND (u.phone LIKE %s OR u.name LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    sql += " ORDER BY u.id DESC"
    return ok(db.query(sql, params))


@bp.route("/users", methods=["POST"])
@require_role("admin")
def create_user():
    body = request.get_json(silent=True) or {}
    phone = (body.get("phone") or "").strip()
    password = body.get("password") or "Fw12345678"
    name = (body.get("name") or "").strip()
    role = body.get("role") or "grass"
    unit_id = int(body.get("unitId") or body.get("unit_id") or 0) or 0
    if not phone or len(phone) != 11:
        return fail(400, "手机号格式不正确")
    if role not in ("grass", "mid", "top", "accept", "admin"):
        return fail(400, "角色不合法")
    if role != "admin" and unit_id <= 0:
        return fail(400, "非系统管理员账号必须归属单位")
    if db.query_one("SELECT id FROM fs_app_users WHERE phone=%s" % _p(), (phone,)):
        return fail(409, "该手机号已存在")
    ok_s, msg = check_password_strength(password)
    if not ok_s:
        return fail(400, "默认密码强度不足，请使用复杂密码")
    uid = db.execute("INSERT INTO fs_app_users(phone,password_hash,name,role,unit_id) VALUES(%s,%s,%s,%s,%s)"
                     % (_p(), _p(), _p(), _p(), _p()),
                     (phone, hash_password(password), name or "用户" + phone[-4:], role, unit_id))
    return ok({"id": uid}, "账号已创建")


@bp.route("/users/<int:uid>/status", methods=["POST"])
@require_role("admin")
def toggle_status(uid):
    body = request.get_json(silent=True) or {}
    status = 1 if body.get("status", 1) else 0
    # 停用则提升 token_version 使即时失效
    db.execute("UPDATE fs_app_users SET status=%s, token_version=token_version+1 WHERE id=%s" % (_p(), _p()),
               (status, uid))
    return ok(None, "已更新状态")


@bp.route("/users/<int:uid>/role", methods=["POST"])
@require_role("admin")
def set_role(uid):
    body = request.get_json(silent=True) or {}
    role = (body.get("role") or "").strip()
    if role not in ("grass", "mid", "top", "accept", "admin"):
        return fail(400, "角色不合法")
    if role != "admin":
        u = db.query_one("SELECT unit_id FROM fs_app_users WHERE id=%s" % _p(), (uid,))
        if not u or (u.get("unit_id") or 0) <= 0:
            return fail(400, "该账号尚未归属单位，请先设置单位")
    db.execute("UPDATE fs_app_users SET role=%s, token_version=token_version+1 WHERE id=%s" % (_p(), _p()),
               (role, uid))
    return ok(None, "角色已更新")


@bp.route("/users/<int:uid>/reset-password", methods=["POST"])
@require_role("admin")
def reset_password(uid):
    body = request.get_json(silent=True) or {}
    new_pw = (body.get("newPassword") or "Fw12345678")
    ok_s, msg = check_password_strength(new_pw)
    if not ok_s:
        return fail(400, msg)
    db.execute("UPDATE fs_app_users SET password_hash=%s, token_version=token_version+1 WHERE id=%s" % (_p(), _p()),
               (hash_password(new_pw), uid))
    return ok(None, "密码已重置")


@bp.route("/users/<int:uid>", methods=["PUT"])
@require_role("admin")
def update_user(uid):
    body = request.get_json(silent=True) or {}
    target = db.query_one("SELECT id, role, status, unit_id FROM fs_app_users WHERE id=%s" % _p(), (uid,))
    if not target:
        return fail(404, "账号不存在")
    # 仅允许管理员修改字段：name、role、status、unit_id
    sets, params = [], []
    new_role = target.get("role")
    new_unit = target.get("unit_id") or 0
    if "name" in body:
        new_name = (body.get("name") or "").strip()
        if not new_name:
            return fail(400, "姓名不能为空")
        if len(new_name) > 20:
            return fail(400, "姓名不能超过 20 字")
        sets.append("name=%s" % _p()); params.append(new_name)
    if "role" in body:
        new_role = (body.get("role") or "").strip()
        allowed = {"grass", "mid", "top", "accept", "admin"}
        if new_role not in allowed:
            return fail(400, "角色不合法")
        # 至少保留一个系统管理员
        if target["id"] and new_role != "admin":
            cnt = db.query_one(
                "SELECT COUNT(*) AS c FROM fs_app_users WHERE role='admin' AND status=1")
            if cnt and cnt.get("c", 0) <= 1:
                return fail(400, "至少保留 1 个启用的系统管理员")
        sets.append("role=%s" % _p()); params.append(new_role)
    if "unitId" in body or "unit_id" in body:
        new_unit = int(body.get("unitId") or body.get("unit_id") or 0) or 0
        sets.append("unit_id=%s" % _p()); params.append(new_unit)
    if "status" in body:
        new_status = int(body.get("status") or 0)
        if new_status not in (0, 1):
            return fail(400, "状态不合法")
        if target.get("status") == 1 and new_status == 0:
            cnt = db.query_one(
                "SELECT COUNT(*) AS c FROM fs_app_users WHERE role='admin' AND status=1")
            if cnt and cnt.get("c", 0) <= 1:
                return fail(400, "至少保留 1 个启用的系统管理员")
        sets.append("status=%s" % _p()); params.append(new_status)
    # 最终校验：非系统管理员账号必须归属单位
    if new_role != "admin" and new_unit <= 0:
        return fail(400, "非系统管理员账号必须归属单位")
    if not sets:
        return fail(400, "没有可修改字段")
    params.append(uid)
    db.execute("UPDATE fs_app_users SET " + ", ".join(sets) + " WHERE id=%s" % _p(),
               tuple(params))
    return ok(None, "账号已更新")


@bp.route("/users/<int:uid>", methods=["DELETE"])
@require_role("admin")
def delete_user(uid):
    if uid == request.user_id:
        return fail(400, "不能删除当前登录账号")
    db.execute("DELETE FROM fs_app_users WHERE id=%s" % _p(), (uid,))
    db.execute("DELETE FROM fs_wechat_bind WHERE user_id=%s" % _p(), (uid,))
    return ok(None, "账号已删除")
