# -*- coding: utf-8 -*-
"""
数据库访问层：MySQL(默认) / SQLite(开发回退)
提供统一 connect / query / execute，返回字典行
"""
import sqlite3
import threading
from datetime import datetime

from config import FS_DB_DSN, FS_DB_ENGINE

_local = threading.local()


def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _connect():
    if FS_DB_ENGINE == "mysql":
        import pymysql
        # 解析 DSN: mysql+pymysql://user:pass@host:port/db?charset=...
        dsn = FS_DB_DSN.replace("mysql+pymysql://", "").replace("mysql://", "")
        if "?" in dsn:
            dsn = dsn.split("?")[0]
        userinfo, hostpart = dsn.rsplit("@", 1)
        if ":" in userinfo:
            user, password = userinfo.split(":", 1)
        else:
            user, password = userinfo, ""
        if "/" in hostpart:
            hostport, dbname = hostpart.split("/", 1)
        else:
            hostport, dbname = hostpart, ""
        host = hostport
        port = 3306
        if ":" in hostport:
            host, port = hostport.split(":", 1)
            port = int(port)
        return pymysql.connect(host=host, port=port, user=user, password=password,
                               database=dbname, charset="utf8mb4",
                               cursorclass=pymysql.cursors.DictCursor,
                               autocommit=True)
    else:
        conn = sqlite3.connect(FS_DB_DSN or
                               "fs_standalone.db",
                               check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def get_conn():
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _connect()
        _local.conn = conn
    return conn


def close():
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
        _local.conn = None


# ---------- 占位符适配（SQLite 用 ?，MySQL 用 %s） ----------
def _ph(n):
    if FS_DB_ENGINE == "mysql":
        return ", ".join(["%s"] * n)
    return ", ".join(["?"] * n)


def _ph_one():
    return "%s" if FS_DB_ENGINE == "mysql" else "?"


def query(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    try:
        if FS_DB_ENGINE == "mysql":
            cur.execute(sql, params or ())
        else:
            cur.execute(sql, params or ())
        if FS_DB_ENGINE == "mysql":
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        else:
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        cur.close()


def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()


def executemany(sql, seq):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.executemany(sql, seq)
        conn.commit()
    finally:
        cur.close()


def init_schema():
    """SQLite 场景自动建表（MySQL 用 schema.sql 导入）"""
    if FS_DB_ENGINE == "mysql":
        return
    sql = open("schema.sql", encoding="utf-8").read()
    # 拆分为单条语句
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    conn = get_conn()
    cur = conn.cursor()
    for st in statements:
        # 去掉 CREATE DATABASE / USE
        if st.upper().startswith("CREATE DATABASE") or st.upper().startswith("USE "):
            continue
        try:
            cur.execute(st)
        except Exception as e:
            # 已存在则忽略
            if "already exists" not in str(e).lower():
                raise
    conn.commit()
    cur.close()
