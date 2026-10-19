# -*- coding: utf-8 -*-
"""
管理端业务路由：单位/楼宇/场所 CRUD、检查标准/法规 CRUD、台账/验收/督办/抽考/快检/照片墙/日报查询
仅 admin 角色可访问，url_prefix = /api/fs/admin
"""
import json
from datetime import datetime, timedelta

from flask import Blueprint, request

import db
from auth import ok, fail, require_role, collect_subtree_unit_ids

bp = Blueprint("manage", __name__, url_prefix="/api/fs/admin")
_p = lambda: "?" if db.FS_DB_ENGINE != "mysql" else "%s"
_today = lambda: datetime.now().strftime("%Y-%m-%d")


def _attach_org(rows):
    """为业务结果行附加单位/楼宇/场所名称（unit_name/building_name/place_name）"""
    for r in rows:
        uid, bid, pid = r.get("unit_id", 0), r.get("building_id", 0), r.get("place_id", 0)
        r["unit_name"] = ""
        r["building_name"] = ""
        r["place_name"] = ""
        if uid:
            u = db.query_one("SELECT name FROM fs_units WHERE id=%s" % _p(), (uid,))
            if u:
                r["unit_name"] = u["name"]
        if bid:
            b = db.query_one("SELECT name FROM fs_buildings WHERE id=%s" % _p(), (bid,))
            if b:
                r["building_name"] = b["name"]
        if pid:
            p = db.query_one("SELECT name FROM fs_places WHERE id=%s" % _p(), (pid,))
            if p:
                r["place_name"] = p["name"]
    return rows


# ============================================================
# 单位
# ============================================================
def _resolve_level(parent_id):
    """根据上级单位计算层级：顶级=1（省公司），否则父级 level+1，封顶 3。"""
    if not parent_id:
        return 1
    parent = db.query_one("SELECT level FROM fs_units WHERE id=%s" % _p(), (parent_id,))
    if not parent:
        return 1
    lv = int(parent.get("level") or 1) + 1
    return lv if lv <= 3 else 3


def _is_descendant(root_id, target_id):
    """判断 target_id 是否为 root_id 的后代（向上追溯 parent 链）。用于防止把单位挂到自己的下级上。"""
    cur = target_id
    seen = set()
    while cur and cur not in seen:
        if cur == root_id:
            return True
        seen.add(cur)
        r = db.query_one("SELECT parent_id FROM fs_units WHERE id=%s" % _p(), (cur,))
        if not r:
            break
        cur = r.get("parent_id") or 0
    return False


@bp.route("/units", methods=["GET"])
@require_role("admin")
def list_units():
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM fs_units WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE %s OR code LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    sql += " ORDER BY level, sort, id"
    rows = db.query(sql, params)
    name_map = {r["id"]: r["name"] for r in rows}
    for r in rows:
        r["parent_name"] = name_map.get(r.get("parent_id") or 0, "")
        r["building_count"] = (db.query_one(
            "SELECT COUNT(*) AS c FROM fs_buildings WHERE unit_id=%s" % _p(), (r["id"],)) or {}).get("c", 0)
        r["place_count"] = (db.query_one(
            "SELECT COUNT(*) AS c FROM fs_places WHERE unit_id=%s" % _p(), (r["id"],)) or {}).get("c", 0)
    return ok(rows)


@bp.route("/units", methods=["POST"])
@require_role("admin")
def create_unit():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "单位名称不能为空")
    parent_id = int(body.get("parentId") or 0) or 0
    level = _resolve_level(parent_id)
    if parent_id:
        if not db.query_one("SELECT id FROM fs_units WHERE id=%s" % _p(), (parent_id,)):
            return fail(400, "上级单位不存在")
        if level > 3:
            return fail(400, "单位层级最多三级（省/市/区县）")
    db.execute(
        "INSERT INTO fs_units(name,code,parent_id,level,contact,phone,address,remark,enabled,sort) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (name, body.get("code", "").strip(), parent_id, level,
         body.get("contact", "").strip(), body.get("phone", "").strip(),
         body.get("address", "").strip(), body.get("remark", "").strip(),
         1 if body.get("enabled", True) else 0, int(body.get("sort") or 0)))
    return ok(None, "单位已新增")


@bp.route("/units/<int:uid>", methods=["PUT"])
@require_role("admin")
def update_unit(uid):
    row = db.query_one("SELECT id, parent_id, level FROM fs_units WHERE id=%s" % _p(), (uid,))
    if not row:
        return fail(404, "单位不存在")
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "单位名称不能为空")
    parent_id = row.get("parent_id") or 0
    level = row.get("level") or 1
    if "parentId" in body:
        parent_id = int(body.get("parentId") or 0) or 0
        if parent_id == uid:
            return fail(400, "上级单位不能是自己")
        if parent_id:
            if not db.query_one("SELECT id FROM fs_units WHERE id=%s" % _p(), (parent_id,)):
                return fail(400, "上级单位不存在")
            if _is_descendant(uid, parent_id):
                return fail(400, "上级单位不能是自己的下级单位")
            level = _resolve_level(parent_id)
            if level > 3:
                return fail(400, "单位层级最多三级（省/市/区县）")
        else:
            level = 1
    db.execute(
        "UPDATE fs_units SET name=%s,code=%s,parent_id=%s,level=%s,contact=%s,phone=%s,address=%s,remark=%s,enabled=%s,sort=%s WHERE id=%s"
        % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (name, body.get("code", "").strip(), parent_id, level,
         body.get("contact", "").strip(), body.get("phone", "").strip(),
         body.get("address", "").strip(), body.get("remark", "").strip(),
         1 if body.get("enabled", True) else 0, int(body.get("sort") or 0), uid))
    return ok(None, "单位已更新")


@bp.route("/units/<int:uid>", methods=["DELETE"])
@require_role("admin")
def delete_unit(uid):
    row = db.query_one("SELECT id FROM fs_units WHERE id=%s" % _p(), (uid,))
    if not row:
        return fail(404, "单位不存在")
    ccount = (db.query_one("SELECT COUNT(*) AS c FROM fs_units WHERE parent_id=%s" % _p(), (uid,)) or {}).get("c", 0)
    if ccount:
        return fail(400, "该单位下存在 %s 个下级单位，请先删除下级单位" % ccount)
    bcount = (db.query_one("SELECT COUNT(*) AS c FROM fs_buildings WHERE unit_id=%s" % _p(), (uid,)) or {}).get("c", 0)
    if bcount:
        return fail(400, "该单位下存在 %s 栋楼宇，请先删除楼宇" % bcount)
    ucount = (db.query_one("SELECT COUNT(*) AS c FROM fs_app_users WHERE unit_id=%s" % _p(), (uid,)) or {}).get("c", 0)
    if ucount:
        return fail(400, "该单位下存在 %s 个账号，请先调整账号归属" % ucount)
    db.execute("DELETE FROM fs_units WHERE id=%s" % _p(), (uid,))
    return ok(None, "单位已删除")


# ============================================================
# 楼宇
# ============================================================
@bp.route("/buildings", methods=["GET"])
@require_role("admin")
def list_buildings():
    unit_id = request.args.get("unitId", "").strip()
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM fs_buildings WHERE 1=1"
    params = []
    if unit_id:
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if q:
        sql += " AND (name LIKE %s OR code LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    sql += " ORDER BY sort, id DESC"
    rows = db.query(sql, params)
    unit_ids = list({r["unit_id"] for r in rows if r["unit_id"]})
    units = {}
    if unit_ids:
        marks = db._ph(len(unit_ids))
        for u in db.query("SELECT id,name FROM fs_units WHERE id IN (%s)" % marks, tuple(unit_ids)):
            units[u["id"]] = u["name"]
    for r in rows:
        r["unit_name"] = units.get(r["unit_id"], "")
        r["place_count"] = (db.query_one(
            "SELECT COUNT(*) AS c FROM fs_places WHERE building_id=%s" % _p(), (r["id"],)) or {}).get("c", 0)
    return ok(rows)


@bp.route("/buildings", methods=["POST"])
@require_role("admin")
def create_building():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "楼宇名称不能为空")
    db.execute(
        "INSERT INTO fs_buildings(unit_id,name,code,floors,address,remark,enabled,sort) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
        % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (int(body.get("unitId") or 0), name, body.get("code", "").strip(),
         int(body.get("floors") or 0), body.get("address", "").strip(),
         body.get("remark", "").strip(), 1 if body.get("enabled", True) else 0,
         int(body.get("sort") or 0)))
    return ok(None, "楼宇已新增")


@bp.route("/buildings/<int:bid>", methods=["PUT"])
@require_role("admin")
def update_building(bid):
    row = db.query_one("SELECT id FROM fs_buildings WHERE id=%s" % _p(), (bid,))
    if not row:
        return fail(404, "楼宇不存在")
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "楼宇名称不能为空")
    db.execute(
        "UPDATE fs_buildings SET unit_id=%s,name=%s,code=%s,floors=%s,address=%s,remark=%s,enabled=%s,sort=%s WHERE id=%s"
        % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (int(body.get("unitId") or 0), name, body.get("code", "").strip(),
         int(body.get("floors") or 0), body.get("address", "").strip(),
         body.get("remark", "").strip(), 1 if body.get("enabled", True) else 0,
         int(body.get("sort") or 0), bid))
    return ok(None, "楼宇已更新")


@bp.route("/buildings/<int:bid>", methods=["DELETE"])
@require_role("admin")
def delete_building(bid):
    row = db.query_one("SELECT id FROM fs_buildings WHERE id=%s" % _p(), (bid,))
    if not row:
        return fail(404, "楼宇不存在")
    pcount = (db.query_one("SELECT COUNT(*) AS c FROM fs_places WHERE building_id=%s" % _p(), (bid,)) or {}).get("c", 0)
    if pcount:
        return fail(400, "该楼宇下存在 %s 个场所，请先删除场所" % pcount)
    db.execute("DELETE FROM fs_buildings WHERE id=%s" % _p(), (bid,))
    return ok(None, "楼宇已删除")


# ============================================================
# 场所
# ============================================================
@bp.route("/places", methods=["GET"])
@require_role("admin")
def list_places():
    unit_id = request.args.get("unitId", "").strip()
    building_id = request.args.get("buildingId", "").strip()
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM fs_places WHERE 1=1"
    params = []
    if unit_id:
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id:
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if q:
        sql += " AND (name LIKE %s OR code LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    sql += " ORDER BY sort, id DESC"
    rows = db.query(sql, params)
    unit_ids = list({r["unit_id"] for r in rows if r["unit_id"]})
    bld_ids = list({r["building_id"] for r in rows if r["building_id"]})
    units, blds = {}, {}
    if unit_ids:
        for u in db.query("SELECT id,name FROM fs_units WHERE id IN (%s)" % db._ph(len(unit_ids)), tuple(unit_ids)):
            units[u["id"]] = u["name"]
    if bld_ids:
        for b in db.query("SELECT id,name FROM fs_buildings WHERE id IN (%s)" % db._ph(len(bld_ids)), tuple(bld_ids)):
            blds[b["id"]] = b["name"]
    for r in rows:
        r["unit_name"] = units.get(r["unit_id"], "")
        r["building_name"] = blds.get(r["building_id"], "")
    return ok(rows)


@bp.route("/places", methods=["POST"])
@require_role("admin")
def create_place():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "场所名称不能为空")
    db.execute(
        "INSERT INTO fs_places(unit_id,building_id,name,code,floor,type,remark,enabled,sort) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (int(body.get("unitId") or 0), int(body.get("buildingId") or 0), name,
         body.get("code", "").strip(), body.get("floor", "").strip(),
         body.get("type", "").strip(), body.get("remark", "").strip(),
         1 if body.get("enabled", True) else 0, int(body.get("sort") or 0)))
    return ok(None, "场所已新增")


@bp.route("/places/<int:pid>", methods=["PUT"])
@require_role("admin")
def update_place(pid):
    row = db.query_one("SELECT id FROM fs_places WHERE id=%s" % _p(), (pid,))
    if not row:
        return fail(404, "场所不存在")
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "场所名称不能为空")
    db.execute(
        "UPDATE fs_places SET unit_id=%s,building_id=%s,name=%s,code=%s,floor=%s,type=%s,remark=%s,enabled=%s,sort=%s WHERE id=%s"
        % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (int(body.get("unitId") or 0), int(body.get("buildingId") or 0), name,
         body.get("code", "").strip(), body.get("floor", "").strip(),
         body.get("type", "").strip(), body.get("remark", "").strip(),
         1 if body.get("enabled", True) else 0, int(body.get("sort") or 0), pid))
    return ok(None, "场所已更新")


@bp.route("/places/<int:pid>", methods=["DELETE"])
@require_role("admin")
def delete_place(pid):
    row = db.query_one("SELECT id FROM fs_places WHERE id=%s" % _p(), (pid,))
    if not row:
        return fail(404, "场所不存在")
    db.execute("DELETE FROM fs_places WHERE id=%s" % _p(), (pid,))
    return ok(None, "场所已删除")


# ============================================================
# 检查标准 CRUD
# ============================================================
@bp.route("/check-items", methods=["GET"])
@require_role("admin")
def manage_check_items():
    area = request.args.get("area", "").strip()
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM fs_check_items WHERE 1=1"
    params = []
    if area:
        sql += " AND area LIKE %s" % _p(); params.append("%" + area + "%")
    if q:
        sql += " AND (name LIKE %s OR std LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    sql += " ORDER BY sort, id"
    return ok(db.query(sql, params))


@bp.route("/check-items", methods=["POST"])
@require_role("admin")
def create_check_item():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "检查项名称不能为空")
    db.execute(
        "INSERT INTO fs_check_items(code,name,area,how,std,basis,penalty,fix,period,level,veto,days,role,sort,enabled) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (body.get("code", "").strip(), name, body.get("area", "").strip(),
         body.get("how", "").strip(), body.get("std", "").strip(),
         body.get("basis", "").strip(), body.get("penalty", "").strip(),
         body.get("fix", "").strip(), body.get("period", "daily"),
         body.get("level", "normal"), 1 if body.get("veto") else 0,
         int(body.get("days") or 3), body.get("role", "grass"),
         int(body.get("sort") or 0), 1 if body.get("enabled", True) else 0))
    return ok(None, "检查项已新增")


@bp.route("/check-items/<int:cid>", methods=["PUT"])
@require_role("admin")
def update_check_item(cid):
    row = db.query_one("SELECT id FROM fs_check_items WHERE id=%s" % _p(), (cid,))
    if not row:
        return fail(404, "检查项不存在")
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "检查项名称不能为空")
    db.execute(
        "UPDATE fs_check_items SET code=%s,name=%s,area=%s,how=%s,std=%s,basis=%s,penalty=%s,fix=%s,period=%s,level=%s,veto=%s,days=%s,role=%s,sort=%s,enabled=%s WHERE id=%s"
        % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (body.get("code", "").strip(), name, body.get("area", "").strip(),
         body.get("how", "").strip(), body.get("std", "").strip(),
         body.get("basis", "").strip(), body.get("penalty", "").strip(),
         body.get("fix", "").strip(), body.get("period", "daily"),
         body.get("level", "normal"), 1 if body.get("veto") else 0,
         int(body.get("days") or 3), body.get("role", "grass"),
         int(body.get("sort") or 0), 1 if body.get("enabled", True) else 0, cid))
    return ok(None, "检查项已更新")


@bp.route("/check-items/<int:cid>", methods=["DELETE"])
@require_role("admin")
def delete_check_item(cid):
    row = db.query_one("SELECT id FROM fs_check_items WHERE id=%s" % _p(), (cid,))
    if not row:
        return fail(404, "检查项不存在")
    db.execute("DELETE FROM fs_check_items WHERE id=%s" % _p(), (cid,))
    return ok(None, "检查项已删除")


# ============================================================
# 法规 CRUD
# ============================================================
@bp.route("/law-items", methods=["GET"])
@require_role("admin")
def manage_law_items():
    area = request.args.get("area", "").strip()
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM fs_law_items WHERE 1=1"
    params = []
    if area:
        sql += " AND area LIKE %s" % _p(); params.append("%" + area + "%")
    if q:
        sql += " AND (name LIKE %s OR basis LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    sql += " ORDER BY sort, id"
    return ok(db.query(sql, params))


@bp.route("/law-items", methods=["POST"])
@require_role("admin")
def create_law_item():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "法规名称不能为空")
    db.execute(
        "INSERT INTO fs_law_items(area,name,category,basis,penalty,sort) VALUES(%s,%s,%s,%s,%s,%s)"
        % (_p(), _p(), _p(), _p(), _p(), _p()),
        (body.get("area", "").strip(), name, body.get("category", "").strip(),
         body.get("basis", "").strip(), body.get("penalty", "").strip(),
         int(body.get("sort") or 0)))
    return ok(None, "法规已新增")


@bp.route("/law-items/<int:lid>", methods=["PUT"])
@require_role("admin")
def update_law_item(lid):
    row = db.query_one("SELECT id FROM fs_law_items WHERE id=%s" % _p(), (lid,))
    if not row:
        return fail(404, "法规不存在")
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return fail(400, "法规名称不能为空")
    db.execute(
        "UPDATE fs_law_items SET area=%s,name=%s,category=%s,basis=%s,penalty=%s,sort=%s WHERE id=%s"
        % (_p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (body.get("area", "").strip(), name, body.get("category", "").strip(),
         body.get("basis", "").strip(), body.get("penalty", "").strip(),
         int(body.get("sort") or 0), lid))
    return ok(None, "法规已更新")


@bp.route("/law-items/<int:lid>", methods=["DELETE"])
@require_role("admin")
def delete_law_item(lid):
    row = db.query_one("SELECT id FROM fs_law_items WHERE id=%s" % _p(), (lid,))
    if not row:
        return fail(404, "法规不存在")
    db.execute("DELETE FROM fs_law_items WHERE id=%s" % _p(), (lid,))
    return ok(None, "法规已删除")


# ============================================================
# 台账 / 验收 管理查询
# ============================================================
@bp.route("/ledger", methods=["GET"])
@require_role("admin")
def manage_ledger():
    typ = request.args.get("type", "").strip()
    q = request.args.get("q", "").strip()
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_ledger WHERE 1=1"
    params = []
    if typ:
        sql += " AND type=%s" % _p(); params.append(typ)
    if q:
        sql += " AND (title LIKE %s OR content LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC"
    return ok(_attach_org(db.query(sql, params)))


@bp.route("/ledger/<int:lid>", methods=["DELETE"])
@require_role("admin")
def manage_delete_ledger(lid):
    db.execute("DELETE FROM fs_ledger WHERE id=%s" % _p(), (lid,))
    return ok(None, "已删除")


@bp.route("/acceptance", methods=["GET"])
@require_role("admin")
def manage_acceptance():
    q = request.args.get("q", "").strip()
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_acceptance WHERE 1=1"
    params = []
    if q:
        sql += " AND (project LIKE %s OR note LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC"
    return ok(_attach_org(db.query(sql, params)))


@bp.route("/acceptance/<int:aid>", methods=["DELETE"])
@require_role("admin")
def manage_delete_acceptance(aid):
    db.execute("DELETE FROM fs_acceptance WHERE id=%s" % _p(), (aid,))
    return ok(None, "已删除")


# ============================================================
# 督办 / 抽考 / 快检 / 照片墙 查询
# ============================================================
@bp.route("/supervise", methods=["GET"])
@require_role("admin")
def manage_supervise():
    status = request.args.get("status", "").strip()
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = ("SELECT s.*, h.title AS hazard_title, h.unit_id, h.building_id, h.place_id "
           "FROM fs_supervise_tasks s "
           "LEFT JOIN fs_hazards h ON h.id=s.hazard_id WHERE 1=1")
    params = []
    if status:
        sql += " AND s.status=%s" % _p(); params.append(status)
    if unit_id and unit_id != "0":
        sql += " AND h.unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND h.building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND h.place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY s.id DESC"
    return ok(_attach_org(db.query(sql, params)))


@bp.route("/supervise/<int:sid>/status", methods=["POST"])
@require_role("admin")
def manage_supervise_status(sid):
    body = request.get_json(silent=True) or {}
    status = body.get("status", "")
    if status not in ("assigned", "in_progress", "done", "rejected"):
        return fail(400, "状态不合法")
    db.execute("UPDATE fs_supervise_tasks SET status=%s WHERE id=%s" % (_p(), _p()), (status, sid))
    return ok(None, "状态已更新")


@bp.route("/quiz-records", methods=["GET"])
@require_role("admin")
def manage_quiz_records():
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_quizzes WHERE 1=1"
    params = []
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC LIMIT 500"
    return ok(_attach_org(db.query(sql, params)))


@bp.route("/spot-records", methods=["GET"])
@require_role("admin")
def manage_spot_records():
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_spot_checks WHERE 1=1"
    params = []
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC LIMIT 500"
    return ok(_attach_org(db.query(sql, params)))


@bp.route("/photos", methods=["GET"])
@require_role("admin")
def manage_photos():
    biz_type = request.args.get("bizType", "").strip()
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = ("SELECT id,user_id,biz_type,biz_id,site_id,data_url,caption,"
           "unit_id,building_id,place_id,created_at FROM fs_photos WHERE 1=1")
    params = []
    if biz_type:
        sql += " AND biz_type=%s" % _p(); params.append(biz_type)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC LIMIT 300"
    return ok(_attach_org(db.query(sql, params)))


@bp.route("/photos/<int:pid>", methods=["DELETE"])
@require_role("admin")
def manage_delete_photo(pid):
    db.execute("DELETE FROM fs_photos WHERE id=%s" % _p(), (pid,))
    return ok(None, "已删除")


# ============================================================
# 日报统计（按日期聚合）
# ============================================================
@bp.route("/report", methods=["GET"])
@require_role("admin")
def daily_report():
    date = request.args.get("date", "").strip() or _today()
    ds = "%s 00:00:00" % date
    de = "%s 23:59:59" % date
    today_tasks = db.query("SELECT * FROM fs_tasks WHERE DATE(created_at)=%s" % _p(), (date,))
    tasks_done = sum(1 for t in today_tasks if t["status"] == "done")
    inspections = db.query(
        "SELECT COUNT(*) AS c FROM fs_inspections WHERE created_at>=%s AND created_at<=%s" % (_p(), _p()), (ds, de))
    hazards = db.query("SELECT * FROM fs_hazards WHERE DATE(created_at)=%s" % _p(), (date,))
    hazards_closed = db.query(
        "SELECT COUNT(*) AS c FROM fs_hazards WHERE status='closed' AND DATE(closed_at)=%s" % _p(), (date,))
    ledger = db.query(
        "SELECT COUNT(*) AS c FROM fs_ledger WHERE created_at>=%s AND created_at<=%s" % (_p(), _p()), (ds, de))
    acceptance = db.query(
        "SELECT COUNT(*) AS c FROM fs_acceptance WHERE created_at>=%s AND created_at<=%s" % (_p(), _p()), (ds, de))
    spot = db.query(
        "SELECT COUNT(*) AS c FROM fs_spot_checks WHERE created_at>=%s AND created_at<=%s" % (_p(), _p()), (ds, de))
    quiz = db.query(
        "SELECT COUNT(*) AS c FROM fs_quizzes WHERE created_at>=%s AND created_at<=%s" % (_p(), _p()), (ds, de))
    return ok({
        "date": date,
        "tasksCreated": len(today_tasks),
        "tasksDone": tasks_done,
        "inspections": inspections[0]["c"] if inspections else 0,
        "hazardsCreated": len(hazards),
        "hazardsClosed": hazards_closed[0]["c"] if hazards_closed else 0,
        "ledger": ledger[0]["c"] if ledger else 0,
        "acceptance": acceptance[0]["c"] if acceptance else 0,
        "spotChecks": spot[0]["c"] if spot else 0,
        "quizRecords": quiz[0]["c"] if quiz else 0,
        "hazards": hazards[:20],
        "tasks": today_tasks[:20],
    })


# ============================================================
# 履职看板（各点位健康分排名 + 8 周趋势）
# ============================================================
def _health_score(task_rate, open_hazards, high_hazards, overdue):
    """复用首页健康分公式：任务完成率 40% + 未闭环隐患 30% + 逾期 30%"""
    if open_hazards:
        base = 1.0 - 0.12 * high_hazards - 0.03 * (open_hazards - high_hazards)
        hazard_score = max(0.2, min(1.0, base))
    else:
        hazard_score = 1.0
    overdue_score = max(0.2, 1.0 - 0.15 * overdue) if overdue else 1.0
    return max(0, min(100, int(round(task_rate * 40 + hazard_score * 30 + overdue_score * 30))))


@bp.route("/board", methods=["GET"])
@require_role("admin")
def board():
    """履职看板：各点位（单位）健康分排名 + 8 周趋势"""
    units = db.query("SELECT id, name, level FROM fs_units ORDER BY level, sort, id")
    ranking = []
    for u in units:
        ids = collect_subtree_unit_ids(u["id"])
        marks = db._ph(len(ids))
        tasks = db.query("SELECT * FROM fs_tasks WHERE unit_id IN (%s)" % marks, tuple(ids))
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "done")
        task_rate = done / float(total) if total else 1.0
        hazards = db.query(
            "SELECT * FROM fs_hazards WHERE unit_id IN (%s) AND status != 'closed'" % marks, tuple(ids))
        open_hazards = len(hazards)
        high_hazards = sum(1 for h in hazards if h["level"] == "high")
        overdue = sum(1 for h in hazards if h["deadline"] and str(h["deadline"]) < _today())
        ranking.append({
            "unit_id": u["id"], "unit_name": u["name"], "level": u["level"],
            "score": _health_score(task_rate, open_hazards, high_hazards, overdue),
            "taskRate": int(round(task_rate * 100)),
            "taskTotal": total, "taskDone": done,
            "openHazards": open_hazards, "highHazards": high_hazards, "overdue": overdue,
        })
    ranking.sort(key=lambda x: x["score"])

    # 8 周趋势（全局：每周任务完成率 + 健康分）
    trend = []
    today = datetime.now().date()
    for i in range(7, -1, -1):
        week_end = today - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=6)
        ws = week_start.strftime("%Y-%m-%d")
        we = week_end.strftime("%Y-%m-%d") + " 23:59:59"
        wk_tasks = db.query(
            "SELECT * FROM fs_tasks WHERE due_date >= %s AND due_date <= %s" % (_p(), _p()), (ws, week_end.strftime("%Y-%m-%d")))
        wk_total = len(wk_tasks)
        wk_done = sum(1 for t in wk_tasks if t["status"] == "done")
        wk_rate = wk_done / float(wk_total) if wk_total else 0.0
        wk_hazards = db.query(
            "SELECT * FROM fs_hazards WHERE DATE(created_at) >= %s AND DATE(created_at) <= %s" % (_p(), _p()),
            (ws, week_end.strftime("%Y-%m-%d")))
        new_hazards = len(wk_hazards)
        closed_hazards = sum(1 for h in wk_hazards if h["status"] == "closed")
        wk_score = _health_score(wk_rate, new_hazards, sum(1 for h in wk_hazards if h["level"] == "high"), 0)
        trend.append({
            "week": ws, "taskRate": int(round(wk_rate * 100)),
            "taskTotal": wk_total, "taskDone": wk_done,
            "newHazards": new_hazards, "closedHazards": closed_hazards, "score": wk_score,
        })
    return ok({"ranking": ranking, "trend": trend})


# ============================================================
# 月度报告（一键生成履职情况/问题/措施）
# ============================================================
@bp.route("/monthly-report", methods=["GET"])
@require_role("admin")
def monthly_report():
    month = request.args.get("month", "").strip() or datetime.now().strftime("%Y-%m")
    try:
        y, m = int(month[:4]), int(month[5:7])
    except Exception:
        return fail(400, "月份格式不正确，应为 YYYY-MM")
    ms = "%s 00:00:00" % (month + "-01")
    me = ("%d-01-01 00:00:00" % (y + 1)) if m == 12 else ("%d-%02d-01 00:00:00" % (y, m + 1))

    tasks = db.query("SELECT * FROM fs_tasks WHERE created_at >= %s AND created_at < %s" % (_p(), _p()), (ms, me))
    task_total = len(tasks)
    task_done = sum(1 for t in tasks if t["status"] == "done")
    task_rate = task_done / float(task_total) if task_total else 0.0

    hazards = db.query("SELECT * FROM fs_hazards WHERE created_at >= %s AND created_at < %s" % (_p(), _p()), (ms, me))
    hazard_total = len(hazards)
    hazard_closed = sum(1 for h in hazards if h["status"] == "closed")
    hazard_rate = hazard_closed / float(hazard_total) if hazard_total else 0.0
    open_hazards = sum(1 for h in hazards if h["status"] != "closed")
    high_hazards = sum(1 for h in hazards if h["level"] == "high")
    overdue = sum(1 for h in hazards if h["deadline"] and str(h["deadline"]) < _today() and h["status"] != "closed")

    inspections = (db.query("SELECT COUNT(*) AS c FROM fs_inspections WHERE created_at >= %s AND created_at < %s"
                            % (_p(), _p()), (ms, me)) or [{"c": 0}])[0]["c"]
    ledger = (db.query("SELECT COUNT(*) AS c FROM fs_ledger WHERE created_at >= %s AND created_at < %s"
                       % (_p(), _p()), (ms, me)) or [{"c": 0}])[0]["c"]
    acceptance = (db.query("SELECT COUNT(*) AS c FROM fs_acceptance WHERE created_at >= %s AND created_at < %s"
                           % (_p(), _p()), (ms, me)) or [{"c": 0}])[0]["c"]
    spot_checks = (db.query("SELECT COUNT(*) AS c FROM fs_spot_checks WHERE created_at >= %s AND created_at < %s"
                            % (_p(), _p()), (ms, me)) or [{"c": 0}])[0]["c"]
    quizzes = (db.query("SELECT COUNT(*) AS c FROM fs_quizzes WHERE created_at >= %s AND created_at < %s"
                        % (_p(), _p()), (ms, me)) or [{"c": 0}])[0]["c"]

    score = _health_score(task_rate, open_hazards, high_hazards, overdue)

    # 自动生成履职情况 / 存在问题 / 下一步措施
    summary = ("本月共生成履责任务 %d 项，完成 %d 项，任务完成率 %.0f%%；"
               "发现隐患 %d 处，已闭环 %d 处，隐患闭环率 %.0f%%；"
               "开展巡检 %d 次、台账记录 %d 条、消防验收 %d 次、领导快检 %d 次、员工抽考 %d 人次。"
               "本月消防安全健康分 %d 分。") % (
        task_total, task_done, task_rate * 100,
        hazard_total, hazard_closed, hazard_rate * 100,
        inspections, ledger, acceptance, spot_checks, quizzes, score)

    problems = []
    if task_rate < 0.9:
        problems.append("任务完成率 %.0f%%，低于 90%% 目标，需加强任务督办。" % (task_rate * 100))
    if open_hazards > 0:
        problems.append("仍有 %d 处隐患未闭环，其中重大隐患 %d 处，需限期整改并跟踪销号。" % (open_hazards, high_hazards))
    if overdue > 0:
        problems.append("存在 %d 处逾期隐患，须挂牌督办、明确责任人与整改期限。" % overdue)
    if score < 75:
        problems.append("本月健康分 %d 分，低于 75 分警戒线，需全面排查履职薄弱环节。" % score)
    if not problems:
        problems.append("本月各项指标整体良好，未发现突出问题。")

    measures = []
    if task_rate < 0.9:
        measures.append("对未完成任务逐项梳理，明确责任人，纳入下周重点督办。")
    if open_hazards > 0:
        measures.append("对未闭环隐患实行清单管理，重大隐患由消防安全责任人挂牌督办。")
    if overdue > 0:
        measures.append("逾期隐患限期 3 日内整改完毕，逾期未改的追究相关人员责任。")
    measures.append("下月继续按法定频次开展防火巡查与检查，做好台账留痕。")
    measures.append("组织一次全员消防安全培训与应急疏散演练。")

    return ok({
        "month": month, "score": score,
        "taskTotal": task_total, "taskDone": task_done, "taskRate": int(round(task_rate * 100)),
        "hazardTotal": hazard_total, "hazardClosed": hazard_closed, "hazardRate": int(round(hazard_rate * 100)),
        "openHazards": open_hazards, "highHazards": high_hazards, "overdue": overdue,
        "inspections": inspections, "ledger": ledger, "acceptance": acceptance,
        "spotChecks": spot_checks, "quizzes": quizzes,
        "summary": summary, "problems": problems, "measures": measures,
    })


# ============================================================
# 履职画像（领导到点位前看数据：完成率/整改率/超期/夜间检查/趋势）
# ============================================================
@bp.route("/profile", methods=["GET"])
@require_role("admin")
def profile():
    unit_id = int(request.args.get("unitId") or 0) or 0
    ids = collect_subtree_unit_ids(unit_id) if unit_id else None
    marks = db._ph(len(ids)) if ids else None

    def _filter(alias):
        if not ids:
            return "", []
        return " AND %s IN (%s)" % (alias, marks), list(ids)

    fsql, fargs = _filter("unit_id")
    # 任务完成率（含下级单位）
    tasks = db.query("SELECT * FROM fs_tasks WHERE 1=1" + fsql, fargs)
    task_total = len(tasks)
    task_done = sum(1 for t in tasks if t["status"] == "done")
    task_rate = task_done / float(task_total) if task_total else 0.0

    # 隐患整改率（已闭环 / 全部）
    hazards = db.query("SELECT * FROM fs_hazards WHERE 1=1" + fsql, fargs)
    hazard_total = len(hazards)
    hazard_closed = sum(1 for h in hazards if h["status"] == "closed")
    hazard_rate = hazard_closed / float(hazard_total) if hazard_total else 0.0
    open_hazards = sum(1 for h in hazards if h["status"] != "closed")
    high_hazards = sum(1 for h in hazards if h["level"] == "high")
    overdue = sum(1 for h in hazards if h["deadline"] and str(h["deadline"]) < _today() and h["status"] != "closed")

    # 夜间检查（22:00-06:00 的巡检记录）
    night_inspections = db.query(
        "SELECT COUNT(*) AS c FROM fs_inspections WHERE 1=1" + fsql +
        " AND (HOUR(created_at) >= 22 OR HOUR(created_at) < 6)", fargs)
    night_count = night_inspections[0]["c"] if night_inspections else 0

    # 近 8 周趋势
    trend = []
    today = datetime.now().date()
    for i in range(7, -1, -1):
        week_end = today - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=6)
        ws = week_start.strftime("%Y-%m-%d")
        wk_tasks = db.query(
            "SELECT * FROM fs_tasks WHERE due_date >= %s AND due_date <= %s" + fsql,
            [ws, week_end.strftime("%Y-%m-%d")] + fargs)
        wk_total = len(wk_tasks)
        wk_done = sum(1 for t in wk_tasks if t["status"] == "done")
        trend.append({
            "week": ws, "taskRate": int(round((wk_done / float(wk_total) * 100) if wk_total else 0)),
            "taskTotal": wk_total, "taskDone": wk_done,
        })

    health = _health_score(task_rate, open_hazards, high_hazards, overdue)

    return ok({
        "unitId": unit_id,
        "taskRate": int(round(task_rate * 100)),
        "taskTotal": task_total, "taskDone": task_done,
        "hazardRate": int(round(hazard_rate * 100)),
        "hazardTotal": hazard_total, "hazardClosed": hazard_closed,
        "openHazards": open_hazards, "highHazards": high_hazards, "overdue": overdue,
        "nightInspections": night_count,
        "health": health,
        "trend": trend,
    })


# ============================================================
# 场所档案卡（扫码/打印用：场所信息 + 检查要点）
# ============================================================
@bp.route("/place-card/<int:pid>", methods=["GET"])
@require_role("admin")
def place_card(pid):
    place = db.query_one("SELECT * FROM fs_places WHERE id=%s" % _p(), (pid,))
    if not place:
        return fail(404, "场所不存在")
    unit_name, building_name = "", ""
    if place.get("unit_id"):
        u = db.query_one("SELECT name FROM fs_units WHERE id=%s" % _p(), (place["unit_id"],))
        unit_name = u["name"] if u else ""
    if place.get("building_id"):
        b = db.query_one("SELECT name FROM fs_buildings WHERE id=%s" % _p(), (place["building_id"],))
        building_name = b["name"] if b else ""
    # 检查要点：优先按场所类型匹配检查项，否则返回通用高频项
    typ = place.get("type") or ""
    if typ:
        items = db.query(
            "SELECT name, how, std, level, veto FROM fs_check_items WHERE area LIKE %s ORDER BY sort, id LIMIT 10"
            % _p(), ("%" + typ + "%",))
    if not typ or not items:
        items = db.query(
            "SELECT name, how, std, level, veto FROM fs_check_items ORDER BY sort, id LIMIT 10")
    return ok({
        "place": place, "unit_name": unit_name, "building_name": building_name, "items": items,
    })
