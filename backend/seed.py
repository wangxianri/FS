# -*- coding: utf-8 -*-
"""
种子数据写入脚本：检查标准库 / 法规对照库 / 角色 / 任务模板 / 量化规则 / 验收模板
运行: python seed.py   (幂等，已存在则跳过)
"""
import json
import sys

import db
from db import init_schema
from seed_data import (ROLES, TASK_TEMPLATES, QUANT_RULES, ACCEPT_POINTS,
                       NAV_MATRIX)

# ---------- 检查标准库种子（19 区域代表性，含法规5要素/周期/等级/否决项/整改期限/角色） ----------
CHECK_ITEMS = [
    # 消防控制室
    {"code": "CI-CONT-01", "name": "消防控制室24小时值班，每班不少于2人持证上岗", "area": "消防控制室",
     "how": "查看值班记录与人员到岗情况，核验上岗证", "std": "24h值班，每班≥2人，持证上岗",
     "basis": "GB 25201 第5.2条、《消防法》第21条", "penalty": "《消防法》第60条",
     "fix": "安排持证人员值班，补充值班力量", "period": "daily", "level": "high", "veto": 1, "days": 1, "role": "grass"},
    {"code": "CI-CONT-02", "name": "火灾报警控制器无故障、无屏蔽，联动开关在自动位", "area": "消防控制室",
     "how": "查看控制器面板，检查故障/屏蔽/联动状态", "std": "无火警、无故障、无屏蔽，联动在自动位",
     "basis": "GB 25201 第6章、61号令第25条", "penalty": "《消防法》第60条",
     "fix": "处置故障，恢复自动，消除屏蔽", "period": "twohour", "level": "high", "veto": 1, "days": 1, "role": "grass"},
    {"code": "CI-CONT-03", "name": "值班记录完整，每2小时记录一次", "area": "消防控制室",
     "how": "核对值班记录本", "std": "每2小时记录，内容完整", "basis": "GB 25201 第5.2条",
     "penalty": "", "fix": "补充完善记录", "period": "twohour", "level": "mid", "veto": 0, "days": 1, "role": "grass"},
    # 机房
    {"code": "CI-RM-01", "name": "机房严禁烟火，禁放锂电池和易燃物品", "area": "机房",
     "how": "现场查看，检查烟头、电池、易燃品", "std": "无烟火，无违规存放锂电池与易燃品",
     "basis": "工信部《通信机楼消防安全管理办法》第14条", "penalty": "行业内通报批评",
     "fix": "清理易燃物品，加强禁烟管理", "period": "daily", "level": "high", "veto": 1, "days": 1, "role": "grass"},
    {"code": "CI-RM-02", "name": "交直流电源线与信号线不得混敷，原则上上走线", "area": "机房",
     "how": "检查线缆敷设路径", "std": "三线分离，交直流与信号线不混敷",
     "basis": "工信部《通信机楼消防安全管理办法》第16条第3项", "penalty": "行业内通报批评",
     "fix": "整改线缆，分开敷设", "period": "monthly", "level": "high", "veto": 1, "days": 15, "role": "grass"},
    {"code": "CI-RM-03", "name": "机房内墙及顶棚装修材料为A级，地面不低于B1级", "area": "机房",
     "how": "查看装修材料等级证明", "std": "内墙顶棚A级，地面≥B1级",
     "basis": "GB 55037-2022、GB 50222", "penalty": "《消防法》第60条",
     "fix": "更换不合格装修材料", "period": "yearly", "level": "mid", "veto": 0, "days": 30, "role": "grass"},
    # 气体灭火
    {"code": "CI-GAS-01", "name": "气体灭火系统在自动位，钢瓶压力正常", "area": "气体灭火区",
     "how": "查看手自动开关与钢瓶压力表", "std": "手自动在自动位，钢瓶压力在正常区间",
     "basis": "GB 25201 附录D", "penalty": "《消防法》第60条",
     "fix": "恢复自动位，补充/更换钢瓶", "period": "daily", "level": "high", "veto": 1, "days": 1, "role": "grass"},
    {"code": "CI-GAS-02", "name": "气体灭火防护区密闭良好，喷嘴无堵塞", "area": "气体灭火区",
     "how": "检查防护区门窗密闭与喷嘴", "std": "密闭良好，喷嘴无堵塞",
     "basis": "GB 50370", "penalty": "", "fix": "修复密封，清理喷嘴", "period": "monthly", "level": "mid", "veto": 0, "days": 7, "role": "grass"},
    # 蓄电池室
    {"code": "CI-BAT-01", "name": "蓄电池无鼓包、漏液、过温", "area": "蓄电池室",
     "how": "目测蓄电池外观并测温", "std": "无鼓包、漏液，温度正常",
     "basis": "YD 5002、GB 50444", "penalty": "行业内通报批评",
     "fix": "更换异常蓄电池", "period": "daily", "level": "high", "veto": 0, "days": 3, "role": "grass"},
    {"code": "CI-BAT-02", "name": "蓄电池室独立设置、防爆通风", "area": "蓄电池室",
     "how": "检查蓄电池室设置与通风", "std": "独立设置，防爆通风正常",
     "basis": "YD 5002", "penalty": "", "fix": "完善独立设置与通风", "period": "monthly", "level": "mid", "veto": 0, "days": 15, "role": "grass"},
    # 配电室
    {"code": "CI-PD-01", "name": "配电室无私自使用大功率电器，电烙铁备案管理", "area": "配电室",
     "how": "检查配电室内电器使用", "std": "无违规大功率电器，电烙铁备案且专人管理",
     "basis": "工信部《通信机楼消防安全管理办法》第16条第1项", "penalty": "行业内通报批评",
     "fix": "清理违规电器，完善备案", "period": "weekly", "level": "high", "veto": 1, "days": 3, "role": "grass"},
    # 储油设施
    {"code": "CI-OIL-01", "name": "储油量不超过1立方米，独立防火分隔", "area": "储油设施",
     "how": "检查储油量与防火分隔", "std": "储油量≤1m³，独立防火分隔",
     "basis": "YD 5002", "penalty": "", "fix": "控制储油量，完善防火分隔", "period": "monthly", "level": "high", "veto": 1, "days": 15, "role": "grass"},
    # 疏散通道
    {"code": "CI-ESC-01", "name": "安全出口不少于2个且分散布置，疏散门向疏散方向开启", "area": "疏散通道",
     "how": "检查安全出口数量与开启方向", "std": "≥2个出口，分散布置，门向外开",
     "basis": "GB 55037-2022 第3.3.1条", "penalty": "《消防法》第60条",
     "fix": "增加/改造安全出口", "period": "monthly", "level": "high", "veto": 1, "days": 15, "role": "grass"},
    {"code": "CI-ESC-02", "name": "疏散通道畅通，无堆物、无锁闭", "area": "疏散通道",
     "how": "现场巡查疏散通道", "std": "通道畅通，无堆物、无锁闭、无堵占",
     "basis": "《消防法》第28条", "penalty": "《消防法》第60条",
     "fix": "立即清理占堵", "period": "daily", "level": "high", "veto": 1, "days": 1, "role": "grass"},
    {"code": "CI-ESC-03", "name": "消防救援口净高净宽均≥1.0m，有永久标志", "area": "疏散通道",
     "how": "检查沿外墙消防救援口", "std": "净高净宽≥1.0m，有内外可识别标志",
     "basis": "GB 55037-2022 第2.2.3条", "penalty": "《消防法》第60条",
     "fix": "改造消防救援口，设置标志", "period": "yearly", "level": "high", "veto": 1, "days": 30, "role": "grass"},
    # 防火分隔
    {"code": "CI-FS-01", "name": "防火墙、防火隔墙完好，无擅自开洞拆除", "area": "防火分隔",
     "how": "检查防火墙完整性", "std": "防火墙完好，无擅自开洞拆除",
     "basis": "GB 55037-2022 第3.3.1、3.3.2条", "penalty": "《消防法》第60条",
     "fix": "恢复防火墙完整性", "period": "monthly", "level": "high", "veto": 1, "days": 15, "role": "grass"},
    {"code": "CI-FS-02", "name": "防火门具有自动关闭功能且具烟密闭性能", "area": "防火分隔",
     "how": "测试防火门自动关闭与密闭", "std": "自动关闭，烟密闭性能良好",
     "basis": "GB 55037-2022 第6.4.1条", "penalty": "《消防法》第60条",
     "fix": "维修或更换防火门", "period": "monthly", "level": "high", "veto": 1, "days": 15, "role": "grass"},
    # 灭火器
    {"code": "CI-ME-01", "name": "灭火器配置充足，压力正常，在有效期内", "area": "灭火器",
     "how": "检查灭火器配置、压力、有效期", "std": "配置充足，压力绿区，在有效期内",
     "basis": "GB 50444、61号令第29条", "penalty": "《消防法》第60条",
     "fix": "补充/更换灭火器", "period": "monthly", "level": "mid", "veto": 0, "days": 7, "role": "grass"},
    # 消火栓
    {"code": "CI-HY-01", "name": "消火栓栓口动压正常（0.35MPa）", "area": "消火栓",
     "how": "开阀测试栓口压力", "std": "栓口动压0.35MPa，水带水枪齐全",
     "basis": "GB 50974", "penalty": "", "fix": "检修消火栓系统", "period": "monthly", "level": "mid", "veto": 0, "days": 7, "role": "grass"},
    # 防排烟
    {"code": "CI-EXH-01", "name": "防烟排烟系统运行正常，防火阀动作正常", "area": "防排烟",
     "how": "测试风机与防火阀", "std": "风机运行正常，防火阀动作灵活",
     "basis": "GB 51251", "penalty": "", "fix": "检修防排烟系统", "period": "quarterly", "level": "mid", "veto": 0, "days": 30, "role": "grass"},
    # 应急照明
    {"code": "CI-EIL-01", "name": "应急照明与疏散指示正常，备用电源≥30min", "area": "应急照明",
     "how": "断电测试应急照明", "std": "应急点亮，备用电源≥30min",
     "basis": "GB 51309", "penalty": "", "fix": "更换损坏灯具/电池", "period": "monthly", "level": "mid", "veto": 0, "days": 7, "role": "grass"},
    # 动火作业
    {"code": "CI-FIRE-01", "name": "动火作业有审批、持证、监护、随工", "area": "动火作业",
     "how": "检查动火审批手续与现场", "std": "审批齐全，持证作业，专人监护，机楼随工",
     "basis": "工信部《通信机楼消防安全管理办法》第17条", "penalty": "行业内通报批评",
     "fix": "补齐手续，落实监护随工", "period": "ondemand", "level": "high", "veto": 1, "days": 1, "role": "grass"},
]

# ---------- 法规对照库种子（5 部法律/规章 + 重点条款） ----------
LAW_ITEMS = [
    {"area": "消防法", "name": "《中华人民共和国消防法》第16条", "category": "法律",
     "basis": "单位应当落实消防安全责任制，定期组织防火检查和巡查，及时消除火灾隐患。",
     "penalty": "第60条：单位违反本法规定的，责令改正，处五千元以上五万元以下罚款。"},
    {"area": "消防法", "name": "《中华人民共和国消防法》第21条", "category": "法律",
     "basis": "自动消防系统的操作人员必须持证上岗，并遵守消防安全操作规程。",
     "penalty": ""},
    {"area": "消防法", "name": "《中华人民共和国消防法》第28条", "category": "法律",
     "basis": "任何单位、个人不得损坏、挪用或者擅自拆除、停用消防设施、器材，不得占用、堵塞、封闭疏散通道、安全出口、消防车通道。",
     "penalty": "第60条"},
    {"area": "61号令", "name": "《机关、团体、企业、事业单位消防安全管理规定》（公安部令第61号）第25条", "category": "部门规章",
     "basis": "消防安全重点单位应当进行每日防火巡查。",
     "penalty": ""},
    {"area": "61号令", "name": "第26条", "category": "部门规章",
     "basis": "机关、团体、事业单位应当至少每季度进行一次防火检查，其他单位应当至少每月进行一次防火检查。",
     "penalty": ""},
    {"area": "61号令", "name": "第36条", "category": "部门规章",
     "basis": "单位应当对每名员工每年至少进行一次消防安全培训。",
     "penalty": ""},
    {"area": "61号令", "name": "第40条", "category": "部门规章",
     "basis": "消防安全重点单位应当按照灭火和应急疏散预案，至少每半年进行一次演练。",
     "penalty": ""},
    {"area": "GB55037", "name": "GB 55037-2022《建筑防火通用规范》第6.4.1条", "category": "国家标准",
     "basis": "防火门应具有自动关闭功能，并应具备烟密闭性能。",
     "penalty": ""},
    {"area": "GB55037", "name": "第2.2.3条", "category": "国家标准",
     "basis": "消防救援口净高和净宽均不应小于1.0m，应设置永久性明显标志。",
     "penalty": ""},
    {"area": "GB25201", "name": "GB 25201《建筑消防设施的维护管理》第5.2条", "category": "国家标准",
     "basis": "消防控制室应24小时值班，每班不应少于2人，每2小时记录一次。",
     "penalty": ""},
    {"area": "通信机楼", "name": "工信部《通信机楼消防安全管理办法》第14条", "category": "部门规章",
     "basis": "通信机楼内禁止吸烟，禁止擅自使用明火。",
     "penalty": "行业内通报批评"},
    {"area": "通信机楼", "name": "第16条", "category": "部门规章",
     "basis": "严禁擅自使用大功率电器；交直流电源线与信号线不得混敷。",
     "penalty": "行业内通报批评"},
]


def seed():
    init_schema()
    # 角色
    for r in ROLES:
        exist = db.query_one("SELECT id FROM fs_roles WHERE role_key=%s" % (
            "?" if db.FS_DB_ENGINE != "mysql" else "%s"), (r["role_key"],))
        if not exist:
            db.execute("INSERT INTO fs_roles(role_key,name,modules,is_system) VALUES(%s,%s,%s,1)" % (
                "?" if db.FS_DB_ENGINE != "mysql" else "%s", "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                "?" if db.FS_DB_ENGINE != "mysql" else "%s"),
                (r["role_key"], r["name"], json.dumps(r["modules"], ensure_ascii=False)))
    # 检查项
    for it in CHECK_ITEMS:
        exist = db.query_one("SELECT id FROM fs_check_items WHERE code=%s" % (
            "?" if db.FS_DB_ENGINE != "mysql" else "%s"), (it["code"],))
        if not exist:
            db.execute(
                "INSERT INTO fs_check_items(code,name,area,how,std,basis,penalty,fix,period,level,veto,days,role) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                    "?" if db.FS_DB_ENGINE != "mysql" else "%s"),
                (it["code"], it["name"], it["area"], it["how"], it["std"], it["basis"],
                 it["penalty"], it["fix"], it["period"], it["level"], it["veto"], it["days"], it["role"]))
    # 法规
    for la in LAW_ITEMS:
        exist = db.query_one("SELECT id FROM fs_law_items WHERE name=%s" % (
            "?" if db.FS_DB_ENGINE != "mysql" else "%s"), (la["name"],))
        if not exist:
            db.execute("INSERT INTO fs_law_items(area,name,category,basis,penalty) VALUES(%s,%s,%s,%s,%s)" % (
                "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                "?" if db.FS_DB_ENGINE != "mysql" else "%s",
                "?" if db.FS_DB_ENGINE != "mysql" else "%s"),
                (la["area"], la["name"], la["category"], la["basis"], la["penalty"]))
    # 版本号（幂等 upsert）
    _p = "?" if db.FS_DB_ENGINE != "mysql" else "%s"
    exist = db.query_one("SELECT id FROM fs_meta WHERE meta_key=%s" % _p, ("seed_version",))
    if exist:
        db.execute("UPDATE fs_meta SET meta_value=%s WHERE meta_key=%s" % (_p, _p),
                   ("2.0.0", "seed_version"))
    else:
        db.execute("INSERT INTO fs_meta(meta_key,meta_value) VALUES(%s,%s)" % (_p, _p),
                   ("seed_version", "2.0.0"))
    print("[seed] 完成：角色 %d、检查项 %d、法规 %d" % (len(ROLES), len(CHECK_ITEMS), len(LAW_ITEMS)))


if __name__ == "__main__":
    seed()
