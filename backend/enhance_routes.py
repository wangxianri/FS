# -*- coding: utf-8 -*-
"""
增强路由（P1/P2）：领导十查/深度快检 spot / 隐患督办派单 supervise / 抽考 quiz /
应急处置卡 emg / 设备操作卡 equip / 离线同步 offline
"""
import json

from flask import Blueprint, request

import db
from auth import ok, fail, auth_required, require_role, get_visible_unit_ids, scope_unit_filter

bp = Blueprint("enhance", __name__, url_prefix="/api/fs")
_p = lambda: "?" if db.FS_DB_ENGINE != "mysql" else "%s"


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


# ---------- 组织架构（单位/楼宇/场所，小程序端选择归属用） ----------
@bp.route("/org/units", methods=["GET"])
@auth_required
def org_units():
    ids = get_visible_unit_ids(request.user)
    base = "SELECT id,name,parent_id,level FROM fs_units WHERE enabled=1"
    if ids is None:
        rows = db.query(base + " ORDER BY level,sort,id")
    elif not ids:
        rows = []
    else:
        marks = db._ph(len(ids))
        rows = db.query(base + " AND id IN (%s) ORDER BY level,sort,id" % marks, tuple(ids))
    return ok(rows)


@bp.route("/org/buildings", methods=["GET"])
@auth_required
def org_buildings():
    unit_id = request.args.get("unitId", "0").strip()
    sql = "SELECT id,name,unit_id FROM fs_buildings WHERE enabled=1"
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    sql += " ORDER BY sort,id"
    return ok(db.query(sql, params))


@bp.route("/org/places", methods=["GET"])
@auth_required
def org_places():
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    sql = "SELECT id,name,unit_id,building_id FROM fs_places WHERE enabled=1"
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    sql += " ORDER BY sort,id"
    return ok(db.query(sql, params))


# ---------- 应急处置卡 ----------
@bp.route("/emg/cards", methods=["GET"])
@auth_required
def emg_cards():
    from seed_data import EMG_CARDS
    return ok(EMG_CARDS)


# ---------- 设备操作卡 ----------
@bp.route("/equip/guides", methods=["GET"])
@auth_required
def equip_guides():
    from seed_data import EQUIP_GUIDES
    return ok(EQUIP_GUIDES)


# ---------- 领导十查/深度快检 ----------
@bp.route("/spot/templates", methods=["GET"])
@require_role("top", "admin")
def spot_templates():
    from seed_data import SPOT_TEN, SPOT_DEEP_EXTRA
    return ok({"ten": SPOT_TEN, "deep": SPOT_TEN + SPOT_DEEP_EXTRA})


@bp.route("/spot/check", methods=["POST"])
@require_role("top", "admin")
def spot_check():
    body = request.get_json(silent=True) or {}
    mode = body.get("mode", "ten")
    site_id = body.get("siteId", "")
    site_name = body.get("siteName", "")
    items = body.get("items") or []
    pass_count = sum(1 for it in items if it.get("pass"))
    fail_count = len(items) - pass_count
    result = "合格" if fail_count == 0 else ("不合格" if any(not it.get("pass") and it.get("veto") for it in items) else "需整改")
    uid = int(body.get("unitId") or 0)
    bid = int(body.get("buildingId") or 0)
    pid = int(body.get("placeId") or 0)
    db.execute("INSERT INTO fs_spot_checks(mode,site_id,site_name,unit_id,building_id,place_id,items,pass_count,fail_count,result,conclusion,user_id,user_name) "
               "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
               (mode, site_id, site_name, uid, bid, pid, json.dumps(items, ensure_ascii=False),
                pass_count, fail_count, result, body.get("conclusion", ""),
                request.user_id, request.user.get("name", "")))
    return ok({"pass": pass_count, "fail": fail_count, "result": result}, "快检已提交")


@bp.route("/spot/records", methods=["GET"])
@require_role("top", "admin")
def spot_records():
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_spot_checks WHERE 1=1"
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC LIMIT 300"
    return ok(_attach_org(db.query(sql, params)))


# ---------- 隐患督办派单 ----------
@bp.route("/supervise", methods=["POST"])
@require_role("mid", "admin")
def create_supervise():
    body = request.get_json(silent=True) or {}
    hazard_id = int(body.get("hazardId") or 0)
    if not hazard_id:
        return fail(400, "缺少隐患")
    from datetime import datetime
    deadline = body.get("deadline") or datetime.now().strftime("%Y-%m-%d")
    db.execute("INSERT INTO fs_supervise_tasks(hazard_id,assignee_id,assignee_name,deadline,note,status,creator_id) "
               "VALUES(%s,%s,%s,%s,%s,'assigned',%s)" % (_p(), _p(), _p(), _p(), _p(), _p()),
               (hazard_id, int(body.get("assigneeId") or 0), body.get("assigneeName", ""),
                deadline, body.get("note", ""), request.user_id))
    return ok(None, "督办单已下发")


@bp.route("/supervise", methods=["GET"])
@require_role("mid", "top", "admin")
def list_supervise():
    scope_sql, scope_params = scope_unit_filter(request.user, "h.unit_id")
    sql = ("SELECT s.*, h.title AS hazard_title FROM fs_supervise_tasks s "
           "LEFT JOIN fs_hazards h ON h.id=s.hazard_id WHERE 1=1" + scope_sql + " ORDER BY s.id DESC")
    return ok(db.query(sql, scope_params))


@bp.route("/supervise/<int:sid>/status", methods=["POST"])
@require_role("mid", "admin")
def update_supervise(sid):
    body = request.get_json(silent=True) or {}
    db.execute("UPDATE fs_supervise_tasks SET status=%s WHERE id=%s" % (_p(), _p()),
               (body.get("status", "in_progress"), sid))
    return ok(None, "状态已更新")


# ---------- 抽考 ----------
@bp.route("/quiz/questions", methods=["GET"])
@require_role("mid", "top", "admin")
def quiz_questions():
    from seed_data import QUIZ_QUESTIONS
    # 判断题作答时返回去掉答案
    return ok(QUIZ_QUESTIONS)


@bp.route("/quiz/submit", methods=["POST"])
@require_role("mid", "top", "admin")
def quiz_submit():
    body = request.get_json(silent=True) or {}
    from seed_data import QUIZ_QUESTIONS
    answers = body.get("answers") or []          # [{index, answer}]
    correct = 0
    detail = []
    for a in answers:
        idx = int(a.get("index"))
        ans = bool(a.get("answer"))
        ref = QUIZ_QUESTIONS[idx]
        is_correct = (ans == ref["ans"])
        if is_correct:
            correct += 1
        detail.append({"index": idx, "answer": ans, "correct": ref["ans"],
                       "isCorrect": is_correct, "explain": ref["explain"]})
    total = len(answers)
    uid = int(body.get("unitId") or 0)
    bid = int(body.get("buildingId") or 0)
    pid = int(body.get("placeId") or 0)
    db.execute("INSERT INTO fs_quizzes(quizzer_id,employee_name,unit_id,building_id,place_id,questions,score,total) "
               "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)" % (_p(), _p(), _p(), _p(), _p(), _p(), _p(), _p()),
               (request.user_id, body.get("employeeName", ""), uid, bid, pid,
                json.dumps(detail, ensure_ascii=False), correct, total))
    return ok({"correct": correct, "total": total, "detail": detail}, "成绩已记录")


@bp.route("/quiz/records", methods=["GET"])
@require_role("mid", "top", "admin")
def quiz_records():
    unit_id = request.args.get("unitId", "0").strip()
    building_id = request.args.get("buildingId", "0").strip()
    place_id = request.args.get("placeId", "0").strip()
    sql = "SELECT * FROM fs_quizzes WHERE 1=1"
    params = []
    scope_sql, scope_params = scope_unit_filter(request.user, "unit_id")
    sql += scope_sql; params.extend(scope_params)
    if unit_id and unit_id != "0":
        sql += " AND unit_id=%s" % _p(); params.append(int(unit_id))
    if building_id and building_id != "0":
        sql += " AND building_id=%s" % _p(); params.append(int(building_id))
    if place_id and place_id != "0":
        sql += " AND place_id=%s" % _p(); params.append(int(place_id))
    sql += " ORDER BY id DESC LIMIT 300"
    return ok(_attach_org(db.query(sql, params)))


# ---------- 离线同步（幂等去重） ----------
@bp.route("/offline/sync", methods=["POST"])
@auth_required
def offline_sync():
    body = request.get_json(silent=True) or {}
    ops = body.get("ops") or []          # [{clientId, action, payload}]
    applied = []
    skipped = []
    for op in ops:
        client_id = op.get("clientId") or ""
        action = op.get("action") or ""
        if not client_id:
            continue
        exist = db.query_one("SELECT id FROM fs_offline_sync_log WHERE client_id=%s" % _p(), (client_id,))
        if exist:
            skipped.append(client_id)
            continue
        # 应用本地积压操作（此处支持 hazard 上报）
        try:
            payload = op.get("payload") or {}
            if action == "hazard":
                db.execute("INSERT INTO fs_hazards(title,area,unit_id,building_id,place_id,level,`desc`,status,reporter_id,reporter_name,deadline) "
                           "VALUES(%s,%s,%s,%s,%s,%s,%s,'open',%s,%s,DATE_ADD(NOW(), INTERVAL 3 DAY))"
                           if db.FS_DB_ENGINE == "mysql" else
                           "INSERT INTO fs_hazards(title,area,unit_id,building_id,place_id,level,`desc`,status,reporter_id,reporter_name,deadline) "
                           "VALUES(%s,%s,%s,%s,%s,%s,%s,'open',%s,%s,datetime('now','+3 days'))",
                           (payload.get("title", ""), payload.get("area", ""),
                            int(payload.get("unitId") or 0), int(payload.get("buildingId") or 0), int(payload.get("placeId") or 0),
                            payload.get("level", "mid"), payload.get("desc", ""),
                            request.user_id, request.user.get("name", "")))
            db.execute("INSERT INTO fs_offline_sync_log(client_id,action,payload,user_id,status) VALUES(%s,%s,%s,%s,'applied')"
                       % (_p(), _p(), _p(), _p()),
                       (client_id, action, json.dumps(payload, ensure_ascii=False), request.user_id))
            applied.append(client_id)
        except Exception:
            db.execute("INSERT INTO fs_offline_sync_log(client_id,action,payload,user_id,status) VALUES(%s,%s,%s,%s,'failed')"
                       % (_p(), _p(), _p(), _p()),
                       (client_id, action, json.dumps(op.get("payload") or {}, ensure_ascii=False), request.user_id))
            skipped.append(client_id)
    return ok({"applied": applied, "skipped": skipped}, "同步完成")
