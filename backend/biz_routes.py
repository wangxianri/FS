# -*- coding: utf-8 -*-
"""
业务路由：任务 / 巡检 / 隐患 / 台账 / 验收 / 检查项 / 法规 / 照片 / 看板 / 速查
基于 EPM fire_safety_workbench.py 业务移植，鉴权改为独立 JWT
"""
import json
from datetime import datetime, timedelta

from flask import Blueprint, request

import db
from auth import ok, fail, auth_required, require_role, get_visible_unit_ids, scope_unit_filter, collect_subtree_unit_ids

bp = Blueprint("biz", __name__, url_prefix="/api/fs")
_p = lambda: "?" if db.FS_DB_ENGINE != "mysql" else "%s"
_today = lambda: datetime.now().strftime("%Y-%m-%d")

# 周期中文映射
PERIOD_NAMES = {"twohour": "每2小时", "shift": "当班", "daily": "每日", "weekly": "每周",
                "monthly": "每月", "quarterly": "每季", "halfyear": "每半年",
                "yearly": "每年", "ondemand": "专项"}
LEVEL_NAMES = {"high": "重大", "mid": "较大", "low": "一般", "normal": "正常"}
STATUS_NAMES = {"open": "未整改", "rectifying": "整改中", "rechecked": "待复查", "closed": "已闭环"}


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
# 检查标准库
# ============================================================
@bp.route("/check-items", methods=["GET"])
@auth_required
def list_check_items():
    area = request.args.get("area", "").strip()
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM fs_check_items WHERE 1=1"
    params = []
    if area:
        sql += " AND area LIKE %s" % _p()
        params.append("%" + area + "%")
    if q:
        sql += " AND (name LIKE %s OR std LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    sql += " AND enabled=1 ORDER BY sort,id"
    rows = db.query(sql, params)
    return ok(rows)


@bp.route("/check-items/<int:cid>", methods=["GET"])
@auth_required
def get_check_item(cid):
    row = db.query_one("SELECT * FROM fs_check_items WHERE id=%s" % _p(), (cid,))
    if not row:
        return fail(404, "检查项不存在")
    return ok(row)


# ============================================================
# 法规对照库
# ============================================================
@bp.route("/reference", methods=["GET"])
@auth_required
def list_law():
    area = request.args.get("area", "").strip()
    q = request.args.get("q", "").strip()
    sql = "SELECT * FROM fs_law_items WHERE 1=1"
    params = []
    if area:
        sql += " AND area LIKE %s" % _p()
        params.append("%" + area + "%")
    if q:
        sql += " AND (name LIKE %s OR basis LIKE %s)" % (_p(), _p())
        kw = "%" + q + "%"
        params.append(kw); params.append(kw)
    sql += " ORDER BY sort,id"
    rows = db.query(sql, params)
    return ok(rows)


@bp.route("/quant", methods=["GET"])
@auth_required
def quant_rules():
    from seed_data import QUANT_RULES
    return ok(QUANT_RULES)


# ============================================================
# 任务
# ============================================================
def _auto_gen_tasks():
    """按 9 类周期自动生成当天应做任务（幂等：同周期同日已有则跳过）"""
    from seed_data import TASK_TEMPLATES
    for tpl in TASK_TEMPLATES:
        period = tpl["period"]
        date_key = _today()
        exist = db.query_one(
            "SELECT id FROM fs_tasks WHERE period=%s AND DATE(created_at)=DATE(%s)" % (_p(), _p()),
            (period, date_key))
        if exist:
            continue
        db.execute(
            "INSERT INTO fs_tasks(code,name,period,area,status,due_date) VALUES(%s,%s,%s,%s,'pending',%s)"
            if db.FS_DB_ENGINE == "mysql" else
            "INSERT INTO fs_tasks(code,name,period,area,status,due_date) VALUES(%s,%s,%s,%s,'pending',%s)",
            (tpl["code"], tpl["name"], period, tpl["area"], _today()))


@bp.route("/tasks", methods=["GET"])
@auth_required
def list_tasks():
    _auto_gen_tasks()
    period = request.args.get("period", "").strip()
    status = request.args.get("status", "").strip()
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_tasks WHERE 1=1"
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if period:
        sql += " AND period=%s" % _p(); params.append(period)
    if status:
        sql += " AND status=%s" % _p(); params.append(status)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY due_date DESC, id DESC"
    rows = db.query(sql, params)
    for r in rows:
        r["periodName"] = PERIOD_NAMES.get(r["period"], r["period"])
    return ok(_attach_org(rows))


@bp.route("/tasks/<int:tid>", methods=["GET"])
@auth_required
def get_task(tid):
    row = db.query_one("SELECT * FROM fs_tasks WHERE id=%s" % _p(), (tid,))
    if not row:
        return fail(404, "任务不存在")
    row["periodName"] = PERIOD_NAMES.get(row["period"], row["period"])
    # 附带检查项模板
    items = db.query("SELECT * FROM fs_check_items WHERE area LIKE %s AND enabled=1" % _p(),
                     ("%" + row["area"] + "%",))
    row["checkItems"] = items
    return ok(row)


@bp.route("/tasks/<int:tid>/inspect", methods=["POST"])
@auth_required
def submit_inspect(tid):
    task = db.query_one("SELECT * FROM fs_tasks WHERE id=%s" % _p(), (tid,))
    if not task:
        return fail(404, "任务不存在")
    body = request.get_json(silent=True) or {}
    area = (body.get("area") or task["area"])
    results = body.get("results") or []
    hazard_title = (body.get("hazardTitle") or "").strip()
    hazard_level = body.get("hazardLevel") or "mid"
    hazard_desc = (body.get("hazardDesc") or "").strip()
    fail_count = sum(1 for r in results if r.get("result") == "fail")
    status = "rectifying" if fail_count > 0 else "done"
    uid = task.get("unit_id", 0) or 0
    bid = task.get("building_id", 0) or 0
    pid = task.get("place_id", 0) or 0
    db.execute("INSERT INTO fs_inspections(task_id,area,unit_id,building_id,place_id,results,fail_count,result_status,user_id) "
               "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
               % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
               (tid, area, uid, bid, pid, json.dumps(results, ensure_ascii=False), fail_count, status, request.user_id))
    db.execute("UPDATE fs_tasks SET status=%s, completed_at=NOW(), score=%s WHERE id=%s"
               if db.FS_DB_ENGINE == "mysql" else
               "UPDATE fs_tasks SET status=%s, completed_at=datetime('now'), score=%s WHERE id=%s",
               (status, max(0, 100 - fail_count * 10), tid))
    # 若存在不合格项且给了隐患标题，自动生成隐患（继承任务归属）
    if fail_count > 0 and hazard_title:
        db.execute("INSERT INTO fs_hazards(title,area,unit_id,building_id,place_id,level,`desc`,status,reporter_id,reporter_name,deadline) "
                   "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'open',%s,%s,DATE_ADD(NOW(), INTERVAL 3 DAY))"
                   if db.FS_DB_ENGINE == "mysql" else
                   "INSERT INTO fs_hazards(title,area,unit_id,building_id,place_id,level,`desc`,status,reporter_id,reporter_name,deadline) "
                   "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'open',%s,%s,datetime('now','+3 days'))",
                   (hazard_title, area, uid, bid, pid, hazard_level, hazard_desc,
                    request.user_id, request.user.get("name", "")))
    return ok({"failCount": fail_count, "status": status}, "巡检已提交")


@bp.route("/tasks/<int:tid>/toggle", methods=["POST"])
@auth_required
def toggle_task(tid):
    """手动创建/关闭 ondemand 专项任务"""
    task = db.query_one("SELECT * FROM fs_tasks WHERE id=%s" % _p(), (tid,))
    if not task:
        return fail(404, "任务不存在")
    new_status = "done" if task["status"] != "done" else "pending"
    db.execute("UPDATE fs_tasks SET status=%s WHERE id=%s" % (_p(), _p()), (new_status, tid))
    return ok({"status": new_status})


@bp.route("/tasks", methods=["POST"])
@require_role("grass", "mid", "admin")
def create_task():
    body = request.get_json(silent=True) or {}
    code = body.get("code") or ("T-O-%s" % int(datetime.now().timestamp()))
    name = body.get("name") or "专项检查任务"
    period = body.get("period") or "ondemand"
    area = body.get("area") or "指定区域"
    uid = int(body.get("unitId") or 0)
    bid = int(body.get("buildingId") or 0)
    pid = int(body.get("placeId") or 0)
    db.execute("INSERT INTO fs_tasks(code,name,period,area,unit_id,building_id,place_id,status,due_date) "
               "VALUES(%s,%s,%s,%s,%s,%s,%s,'pending',%s)"
               if db.FS_DB_ENGINE == "mysql" else
               "INSERT INTO fs_tasks(code,name,period,area,unit_id,building_id,place_id,status,due_date) "
               "VALUES(%s,%s,%s,%s,%s,%s,%s,'pending',%s)",
               (code, name, period, area, uid, bid, pid, _today()))
    return ok(None, "任务已创建")


# ============================================================
# 隐患
# ============================================================
@bp.route("/hazards", methods=["GET"])
@auth_required
def list_hazards():
    status = request.args.get("status", "").strip()
    level = request.args.get("level", "").strip()
    area = request.args.get("area", "").strip()
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_hazards WHERE 1=1"
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if status:
        sql += " AND status=%s" % _p(); params.append(status)
    if level:
        sql += " AND level=%s" % _p(); params.append(level)
    if area:
        sql += " AND area LIKE %s" % _p(); params.append("%" + area + "%")
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC"
    rows = db.query(sql, params)
    for r in rows:
        r["statusName"] = STATUS_NAMES.get(r["status"], r["status"])
        r["levelName"] = LEVEL_NAMES.get(r["level"], r["level"])
    return ok(_attach_org(rows))


@bp.route("/hazards/<int:hid>", methods=["GET"])
@auth_required
def get_hazard(hid):
    row = db.query_one("SELECT * FROM fs_hazards WHERE id=%s" % _p(), (hid,))
    if not row:
        return fail(404, "隐患不存在")
    row["statusName"] = STATUS_NAMES.get(row["status"], row["status"])
    row["levelName"] = LEVEL_NAMES.get(row["level"], row["level"])
    photos = db.query("SELECT * FROM fs_photos WHERE biz_type='hazard' AND biz_id=%s" % _p(), (hid,))
    row["photos"] = photos
    return ok(row)


@bp.route("/hazards", methods=["POST"])
@auth_required
def create_hazard():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return fail(400, "隐患标题不能为空")
    days = int(body.get("days") or 3)
    uid = int(body.get("unitId") or 0)
    bid = int(body.get("buildingId") or 0)
    pid = int(body.get("placeId") or 0)
    db.execute("INSERT INTO fs_hazards(title,area,unit_id,building_id,place_id,level,`desc`,status,reporter_id,reporter_name,deadline,photo_ids) "
               "VALUES(%s,%s,%s,%s,%s,%s,%s,'open',%s,%s,DATE_ADD(NOW(), INTERVAL %s DAY),%s)"
               if db.FS_DB_ENGINE == "mysql" else
               "INSERT INTO fs_hazards(title,area,unit_id,building_id,place_id,level,`desc`,status,reporter_id,reporter_name,deadline,photo_ids) "
               "VALUES(%s,%s,%s,%s,%s,%s,%s,'open',%s,%s,datetime('now','+%s days'),%s)",
               (title, body.get("area", ""), uid, bid, pid, body.get("level", "mid"), body.get("desc", ""),
                request.user_id, request.user.get("name", ""), days,
                ",".join([str(x) for x in (body.get("photoIds") or [])])))
    return ok(None, "隐患已上报")


@bp.route("/hazards/<int:hid>/rectify", methods=["POST"])
@auth_required
def rectify_hazard(hid):
    body = request.get_json(silent=True) or {}
    db.execute("UPDATE fs_hazards SET status='rectifying', rectify_note=%s, assignee_id=%s, assignee_name=%s WHERE id=%s"
               % (_p(), _p(), _p(), _p()),
               (body.get("note", ""), request.user_id, request.user.get("name", ""), hid))
    return ok(None, "已提交整改")


@bp.route("/hazards/<int:hid>/recheck", methods=["POST"])
@auth_required
def recheck_hazard(hid):
    body = request.get_json(silent=True) or {}
    note = body.get("note", "")
    passed = body.get("passed", True)
    new_status = "closed" if passed else "rectifying"
    if passed:
        db.execute("UPDATE fs_hazards SET status='closed', recheck_note=%s, closed_at=%s WHERE id=%s"
                   % (_p(), ("NOW()" if db.FS_DB_ENGINE == "mysql" else "datetime('now')"), _p()),
                   (note, hid))
    else:
        db.execute("UPDATE fs_hazards SET status='rectifying', recheck_note=%s WHERE id=%s" % (_p(), _p()),
                   (note, hid))
    return ok({"status": new_status}, "复查完成")


@bp.route("/hazards/<int:hid>/close", methods=["POST"])
@auth_required
def close_hazard(hid):
    body = request.get_json(silent=True) or {}
    db.execute("UPDATE fs_hazards SET status='closed', close_note=%s, closed_at=%s WHERE id=%s"
               % (_p(), ("NOW()" if db.FS_DB_ENGINE == "mysql" else "datetime('now')"), _p()),
               (body.get("note", ""), hid))
    return ok(None, "隐患已闭环")


@bp.route("/hazards/<int:hid>/reopen", methods=["POST"])
@auth_required
def reopen_hazard(hid):
    db.execute("UPDATE fs_hazards SET status='open' WHERE id=%s" % _p(), (hid,))
    return ok(None, "已重新打开")


@bp.route("/hazards/board", methods=["GET"])
@require_role("mid", "top", "admin")
def hazards_board():
    """隐患看板：按状态/等级/区域聚合"""
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    rows = db.query("SELECT * FROM fs_hazards WHERE 1=1" + scope_sql, scope_params)
    board = {
        "total": len(rows),
        "open": sum(1 for r in rows if r["status"] == "open"),
        "rectifying": sum(1 for r in rows if r["status"] == "rectifying"),
        "rechecked": sum(1 for r in rows if r["status"] == "rechecked"),
        "closed": sum(1 for r in rows if r["status"] == "closed"),
        "high": sum(1 for r in rows if r["level"] == "high"),
        "mid": sum(1 for r in rows if r["level"] == "mid"),
        "low": sum(1 for r in rows if r["level"] == "low"),
        "overdue": sum(1 for r in rows if r["deadline"] and str(r["deadline"]) < _today()
                       and r["status"] != "closed"),
        "areas": {},
        "recent": rows[:10],
    }
    for r in rows:
        a = r["area"] or "未分类"
        board["areas"].setdefault(a, {"total": 0, "open": 0, "closed": 0})
        board["areas"][a]["total"] += 1
        board["areas"][a]["open" if r["status"] != "closed" else "closed"] += 1
    return ok(board)


# ============================================================
# 台账
# ============================================================
@bp.route("/ledger/types", methods=["GET"])
@auth_required
def ledger_types():
    from seed_data import LEDGER_TYPES
    return ok(LEDGER_TYPES)


@bp.route("/ledger", methods=["GET"])
@auth_required
def list_ledger():
    typ = request.args.get("type", "").strip()
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_ledger WHERE 1=1"
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if typ:
        sql += " AND type=%s" % _p(); params.append(typ)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC"
    return ok(_attach_org(db.query(sql, params)))


@bp.route("/ledger", methods=["POST"])
@auth_required
def create_ledger():
    body = request.get_json(silent=True) or {}
    typ = body.get("type", "").strip()
    title = (body.get("title") or "").strip()
    if not title:
        return fail(400, "台账标题不能为空")
    uid = int(body.get("unitId") or 0)
    bid = int(body.get("buildingId") or 0)
    pid = int(body.get("placeId") or 0)
    db.execute("INSERT INTO fs_ledger(type,title,content,unit_id,building_id,place_id,user_id,user_name) "
               "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
               % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
               (typ, title, body.get("content", ""), uid, bid, pid,
                request.user_id, request.user.get("name", "")))
    return ok(None, "台账已添加")


@bp.route("/ledger/<int:lid>", methods=["DELETE"])
@auth_required
def delete_ledger(lid):
    db.execute("DELETE FROM fs_ledger WHERE id=%s" % _p(), (lid,))
    return ok(None, "已删除")


# ============================================================
# 验收
# ============================================================
@bp.route("/acceptance/templates", methods=["GET"])
@auth_required
def accept_templates():
    from seed_data import ACCEPT_POINTS
    return ok(ACCEPT_POINTS)


@bp.route("/acceptance", methods=["GET"])
@require_role("accept", "admin")
def list_acceptance():
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_acceptance WHERE 1=1"
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC"
    return ok(_attach_org(db.query(sql, params)))


@bp.route("/acceptance", methods=["POST"])
@require_role("accept", "admin")
def create_acceptance():
    body = request.get_json(silent=True) or {}
    project = (body.get("project") or "").strip()
    if not project:
        return fail(400, "验收项目不能为空")
    uid = int(body.get("unitId") or 0)
    bid = int(body.get("buildingId") or 0)
    pid = int(body.get("placeId") or 0)
    db.execute("INSERT INTO fs_acceptance(project,result,note,unit_id,building_id,place_id,user_id,user_name) "
               "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
               % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
               (project, body.get("result", "pass"), body.get("note", ""), uid, bid, pid,
                request.user_id, request.user.get("name", "")))
    return ok(None, "验收记录已保存")


# ============================================================
# 照片（随手拍）
# ============================================================
@bp.route("/photos", methods=["POST"])
@auth_required
def upload_photo():
    body = request.get_json(silent=True) or {}
    data_url = body.get("dataUrl") or ""
    if not data_url:
        return fail(400, "缺少图片数据")
    if len(data_url) > 5 * 1024 * 1024:
        return fail(400, "图片过大")
    uid = int(body.get("unitId") or 0)
    bid = int(body.get("buildingId") or 0)
    pid = int(body.get("placeId") or 0)
    pid = db.execute("INSERT INTO fs_photos(user_id,biz_type,biz_id,site_id,unit_id,building_id,place_id,data_url,caption) "
                     "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                     % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
                     (request.user_id, body.get("bizType", ""), int(body.get("bizId") or 0),
                      body.get("siteId", ""), uid, bid, pid, data_url, body.get("caption", "")))
    return ok({"id": pid}, "照片已上传")


@bp.route("/photos", methods=["GET"])
@auth_required
def list_photos():
    biz_type = request.args.get("bizType", "").strip()
    biz_id = request.args.get("bizId", "").strip()
    sql = ("SELECT id,user_id,biz_type,biz_id,site_id,unit_id,building_id,place_id,data_url,caption,created_at "
           "FROM fs_photos WHERE 1=1")
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if biz_type:
        sql += " AND biz_type=%s" % _p(); params.append(biz_type)
    if biz_id:
        sql += " AND biz_id=%s" % _p(); params.append(int(biz_id))
    sql += " ORDER BY id DESC"
    return ok(_attach_org(db.query(sql, params)))


# ============================================================
# 首页聚合
# ============================================================
@bp.route("/home", methods=["GET"])
@auth_required
def home():
    user = request.user
    # ---------- 组织范围筛选（单位/楼宇/场所） ----------
    unit_id = int(request.args.get("unitId") or request.args.get("unit_id") or 0) or 0
    building_id = int(request.args.get("buildingId") or request.args.get("building_id") or 0) or 0
    place_id = int(request.args.get("placeId") or request.args.get("place_id") or 0) or 0

    def _build_org_where(alias, uid, bid, pid):
        """根据所选层级构造 WHERE 片段。
        - 选到 place：严格匹配 place_id
        - 选到 building：严格匹配 building_id
        - 只选 unit：展开为本级+所有下级单位（树形继承，选省公司即看全省）
        """
        wheres = []
        args = []
        if pid:
            wheres.append(f"{alias}.place_id = %s")
            args.append(pid)
        elif bid:
            wheres.append(f"{alias}.building_id = %s")
            args.append(bid)
        elif uid:
            ids = collect_subtree_unit_ids(uid)
            marks = db._ph(len(ids))
            wheres.append(f"{alias}.unit_id IN ({marks})")
            args.extend(ids)
        return ("WHERE " + " AND ".join(wheres)) if wheres else "", args

    task_where_sql, task_args = _build_org_where("t", unit_id, building_id, place_id)
    haz_where_sql, haz_args = _build_org_where("h", unit_id, building_id, place_id)

    # 叠加用户可见范围（非 admin 只能看本级+下级单位数据，安全底线）
    scope_sql_t, scope_params_t = scope_unit_filter(user, "t.unit_id")
    scope_sql_h, scope_params_h = scope_unit_filter(user, "h.unit_id")

    def _combine(where_sql, scope_sql):
        if not where_sql:
            return ("WHERE 1=1" + scope_sql) if scope_sql else ""
        return where_sql + scope_sql

    task_where_sql = _combine(task_where_sql, scope_sql_t)
    haz_where_sql = _combine(haz_where_sql, scope_sql_h)
    task_args.extend(scope_params_t)
    haz_args.extend(scope_params_h)

    task_sql = f"SELECT * FROM fs_tasks t {task_where_sql} ORDER BY due_date DESC, id DESC LIMIT 20"
    haz_sql = f"SELECT * FROM fs_hazards h {haz_where_sql} ORDER BY id DESC LIMIT 20"
    tasks = db.query(task_sql, task_args) if task_args else db.query(task_sql)
    _attach_org(tasks)
    tasks_today = [t for t in tasks if str(t.get("due_date")) == _today()]
    done_today = [t for t in tasks_today if t["status"] == "done"]
    pending_tasks = [t for t in tasks if t["status"] != "done"]
    hazards = db.query(haz_sql, haz_args) if haz_args else db.query(haz_sql)
    open_hazards = [h for h in hazards if h["status"] != "closed"]
    high_hazards = [h for h in open_hazards if h["level"] == "high"]
    overdue = [h for h in hazards if h["deadline"] and str(h["deadline"]) < _today()
               and h["status"] != "closed"]
    # 记录本次筛选范围，方便前端展示
    scope = {"unitId": unit_id, "buildingId": building_id, "placeId": place_id}

    # ---------- 今日日期（大卡片） ----------
    now = datetime.now()
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]
    today = {
        "date": "%d年%d月%d日" % (now.year, now.month, now.day),
        "weekday": weekday_cn,
        "isodate": now.strftime("%Y-%m-%d"),
    }

    # ---------- 健康分（0-100，圆环展示） ----------
    # 综合：今日任务完成率 40% + 未闭环隐患 30% + 逾期隐患 30%
    task_rate = 1.0
    if tasks_today:
        task_rate = len(done_today) / float(len(tasks_today))
    hazard_score = 1.0
    if open_hazards:
        # 重大隐患严重拉低分数
        base = 1.0 - 0.12 * len(high_hazards) - 0.03 * (len(open_hazards) - len(high_hazards))
        hazard_score = max(0.2, min(1.0, base))
    overdue_score = 1.0
    if overdue:
        overdue_score = max(0.2, 1.0 - 0.15 * len(overdue))
    health_raw = int(round((task_rate * 40 + hazard_score * 30 + overdue_score * 30)))
    health_score = max(0, min(100, health_raw))
    # 消防安全形势判定
    if health_score >= 90:
        health_level, health_status = "excellent", "消防安全形势良好"
    elif health_score >= 75:
        health_level, health_status = "good", "消防安全形势稳定"
    elif health_score >= 60:
        health_level, health_status = "fair", "消防安全形势一般"
    else:
        health_level, health_status = "poor", "消防安全形势严峻"

    # ---------- 今日履责任务（按周期分组） ----------
    period_order = ["twohour", "shift", "daily", "weekly", "monthly", "quarterly", "halfyear", "yearly", "ondemand"]
    groups = {}
    for pt in tasks_today:
        per = pt.get("period") or "daily"
        g = groups.setdefault(per, {"period": per, "periodName": PERIOD_NAMES.get(per, per), "tasks": []})
        g["tasks"].append({
            "id": pt["id"], "code": pt["code"], "name": pt["name"],
            "area": pt["area"], "status": pt["status"], "score": pt.get("score", 0),
            "unit_name": pt.get("unit_name", ""), "building_name": pt.get("building_name", ""),
            "place_name": pt.get("place_name", ""),
        })
    periodTasks = []
    for per in period_order:
        if per in groups:
            g = groups[per]
            done = [t for t in g["tasks"] if t["status"] == "done"]
            periodTasks.append({
                "period": per, "periodName": g["periodName"],
                "total": len(g["tasks"]), "done": len(done),
                "tasks": g["tasks"],
            })

    return ok({
        "user": {"name": user["name"], "role": user["role"]},
        "scope": scope,
        "today": today,
        "health": {
            "score": health_score,
            "level": health_level,
            "status": health_status,
            "taskRate": int(round(task_rate * 100)),
        },
        "stats": {
            "todayTasks": len(tasks_today),
            "pendingTasks": len(pending_tasks),
            "openHazards": len(open_hazards),
            "highHazards": len(high_hazards),
            "overdue": len(overdue),
        },
        "periodTasks": periodTasks,
        "tasksToday": tasks_today[:5],
        "recentHazards": hazards[:5],
        "overdueHazards": overdue[:5],
        "version": "2.0.0",
    })


# ============================================================
# 维保与报修（故障闭环：登记→维修中→待验收→已闭环）
# ============================================================
REPAIR_STATUS_NAMES = {"open": "已登记", "repairing": "维修中", "checking": "待验收", "closed": "已闭环"}


@bp.route("/repairs", methods=["GET"])
@auth_required
def list_repairs():
    status = request.args.get("status", "").strip()
    unit_id = request.args.get("unitId", "0").strip()
    sql = "SELECT * FROM fs_repairs WHERE 1=1"
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if status:
        sql += " AND status=%s" % _p(); params.append(status)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    sql += " ORDER BY id DESC"
    rows = _attach_org(db.query(sql, params))
    for r in rows:
        r["statusName"] = REPAIR_STATUS_NAMES.get(r["status"], r["status"])
    return ok(rows)


@bp.route("/repairs", methods=["POST"])
@auth_required
def create_repair():
    body = request.get_json(silent=True) or {}
    device = (body.get("device") or "").strip()
    if not device:
        return fail(400, "设备名称不能为空")
    from datetime import datetime
    code = "WX" + datetime.now().strftime("%Y%m%d%H%M%S")
    db.execute(
        "INSERT INTO fs_repairs(code,device,location,unit_id,building_id,place_id,fault_desc,status,deadline,reporter_id,reporter_name) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,'open',%s,%s,%s)" % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
        (code, device, body.get("location", "").strip(),
         int(body.get("unitId") or 0), int(body.get("buildingId") or 0), int(body.get("placeId") or 0),
         body.get("faultDesc", "").strip(), body.get("deadline") or None,
         request.user_id, request.user.get("name", "")))
    return ok({"code": code}, "报修已登记")


@bp.route("/repairs/<int:rid>/status", methods=["POST"])
@auth_required
def update_repair_status(rid):
    body = request.get_json(silent=True) or {}
    status = body.get("status", "")
    if status not in ("repairing", "checking", "closed", "open"):
        return fail(400, "状态不合法")
    row = db.query_one("SELECT id FROM fs_repairs WHERE id=%s" % _p(), (rid,))
    if not row:
        return fail(404, "报修记录不存在")
    sets = ["status=%s" % _p()]
    params = [status]
    if status == "checking":
        sets.append("repair_note=%s" % _p())
        params.append(body.get("repairNote", "").strip())
    if status == "closed":
        sets.append("check_note=%s" % _p())
        params.append(body.get("checkNote", "").strip())
    params.append(rid)
    db.execute("UPDATE fs_repairs SET " + ", ".join(sets) + " WHERE id=%s" % _p(), tuple(params))
    return ok(None, "状态已更新")


@bp.route("/repairs/<int:rid>", methods=["DELETE"])
@auth_required
def delete_repair(rid):
    db.execute("DELETE FROM fs_repairs WHERE id=%s" % _p(), (rid,))
    return ok(None, "报修记录已删除")


# ============================================================
# 任务下发（节前/重大活动专项任务，一键下发到单位）
# ============================================================
NOTICE_STATUS_NAMES = {"active": "进行中", "done": "已完成", "cancelled": "已取消"}


@bp.route("/notices", methods=["GET"])
@auth_required
def list_notices():
    status = request.args.get("status", "").strip()
    sql = "SELECT * FROM fs_notices WHERE 1=1"
    params = []
    # 数据权限：非 admin 只看下发到本单位及下级单位的通知，外加"全部单位"的公开通知
    ids = get_visible_unit_ids(request.user)
    if ids is not None:
        if not ids:
            sql += " AND unit_id=0"
        else:
            marks = db._ph(len(ids) + 1)
            sql += " AND (unit_id IN (%s) OR unit_id=0)" % marks
            params.extend(ids)
            params.append(0)
    if status:
        sql += " AND status=%s" % _p(); params.append(status)
    sql += " ORDER BY id DESC"
    rows = db.query(sql, params)
    for r in rows:
        r["statusName"] = NOTICE_STATUS_NAMES.get(r["status"], r["status"])
        if r.get("unit_id"):
            u = db.query_one("SELECT name FROM fs_units WHERE id=%s" % _p(), (r["unit_id"],))
            r["unit_name"] = u["name"] if u else ""
        else:
            r["unit_name"] = "全部单位"
    return ok(rows)


@bp.route("/notices", methods=["POST"])
@require_role("mid", "admin")
def create_notice():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return fail(400, "任务标题不能为空")
    unit_id = int(body.get("unitId") or 0) or 0
    db.execute(
        "INSERT INTO fs_notices(title,content,unit_id,deadline,status,creator_id,creator_name) "
        "VALUES(%s,%s,%s,%s,'active',%s,%s)" % (_p(), _p(), _p(), _p(), _p(), _p()),
        (title, body.get("content", "").strip(), unit_id, body.get("deadline") or None,
         request.user_id, request.user.get("name", "")))
    return ok(None, "任务已下发")


@bp.route("/notices/<int:nid>/status", methods=["POST"])
@require_role("mid", "admin")
def update_notice_status(nid):
    body = request.get_json(silent=True) or {}
    status = body.get("status", "")
    if status not in ("done", "cancelled", "active"):
        return fail(400, "状态不合法")
    db.execute("UPDATE fs_notices SET status=%s WHERE id=%s" % (_p(), _p()), (status, nid))
    return ok(None, "状态已更新")


@bp.route("/notices/<int:nid>", methods=["DELETE"])
@require_role("mid", "admin")
def delete_notice(nid):
    db.execute("DELETE FROM fs_notices WHERE id=%s" % _p(), (nid,))
    return ok(None, "已删除")
