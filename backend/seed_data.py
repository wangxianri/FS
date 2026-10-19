# -*- coding: utf-8 -*-
"""
种子数据常量：任务模板 / 角色权限 / 量化规则 / 验收模板 / 处置卡 / 抽考题
（检查项与法规正文由 seed.py 从内置知识库写入）
"""

# ---------- 角色定义与模块权限（前端菜单矩阵，按建设方案「角色与功能对应表」严格互斥） ----------
# 设计原则：
#   - 执行类（今日任务/隐患/台账/应急卡）只给基层
#   - 管理类（履职看板/隐患督办/任务下发/月度报告）只给中层
#   - 决策类（现场快检/履职画像/检查记录）只给领导
#   - 员工抽查：中层（组织）+ 领导（现场考）
#   - 设备操作与维保、检查标准、法规速查：三角色共同知识底座
#   - 维保报修（equip 内子页签）只给中层（前端按 role 控制子页签）
ROLES = [
    {"role_key": "grass", "name": "基层执行",
     "modules": ["home", "tasks", "task-inspect", "hazards", "ledger",
                 "emg", "equip", "check-items", "reference", "photos"]},
    {"role_key": "mid", "name": "中层管理",
     "modules": ["home", "board", "supervise", "report", "notice",
                 "equip", "quiz", "check-items", "reference", "photos"]},
    {"role_key": "top", "name": "领导检查",
     "modules": ["home", "spot", "profile", "records",
                 "equip", "quiz", "check-items", "reference"]},
    {"role_key": "accept", "name": "消防验收",
     "modules": ["home", "acceptance", "check-items", "reference", "photos", "records"]},
    {"role_key": "admin", "name": "系统管理员",
     "modules": ["home", "tasks", "task-inspect", "hazards", "ledger", "acceptance",
                 "check-items", "reference", "photos", "board", "supervise", "spot",
                 "profile", "report", "emg", "equip", "quiz", "admin_users",
                 "records", "notice"]},
]

# 完整导航权限矩阵（页面 -> 允许角色），供后端强校验
NAV_MATRIX = {
    "home": ["grass", "mid", "top", "accept", "admin"],
    "tasks": ["grass", "admin"],
    "task-inspect": ["grass", "admin"],
    "hazards": ["grass", "admin"],
    "ledger": ["grass", "admin"],
    "emg": ["grass", "admin"],
    "acceptance": ["accept", "admin"],
    "check-items": ["grass", "mid", "top", "accept", "admin"],
    "reference": ["grass", "mid", "top", "accept", "admin"],
    "photos": ["grass", "mid", "accept", "admin"],
    "board": ["mid", "admin"],
    "supervise": ["mid", "admin"],
    "report": ["mid", "admin"],
    "notice": ["mid", "admin"],
    "spot": ["top", "admin"],
    "profile": ["top", "admin"],
    "records": ["top", "accept", "admin"],
    "quiz": ["mid", "top", "admin"],
    "equip": ["grass", "mid", "top", "admin"],
    "admin_users": ["admin"],
}

# ---------- 任务模板（9 类周期） ----------
TASK_TEMPLATES = [
    {"code": "T-2H-001", "name": "消控室值班巡查（每2小时）", "period": "twohour", "area": "消防控制室",
     "desc": "控制器状态、手自动开关、值班记录"},
    {"code": "T-SHIFT-001", "name": "当班防火巡查", "period": "shift", "area": "值班区域",
     "desc": "班次交接时防火巡查"},
    {"code": "T-D-001", "name": "每日防火巡查", "period": "daily", "area": "重点部位",
     "desc": "61号令第25条每日防火巡查"},
    {"code": "T-W-001", "name": "每周设备检查", "period": "weekly", "area": "消防设施",
     "desc": "每周消防设施运行状态检查"},
    {"code": "T-M-001", "name": "每月防火检查", "period": "monthly", "area": "全单位",
     "desc": "61号令第26条每月防火检查"},
    {"code": "T-Q-001", "name": "每季综合检查", "period": "quarterly", "area": "全单位",
     "desc": "季度消防安全综合检查"},
    {"code": "T-H-001", "name": "半年灭火疏散演练", "period": "halfyear", "area": "全单位",
     "desc": "61号令第40条每半年演练"},
    {"code": "T-Y-001", "name": "年度建筑消防设施检测", "period": "yearly", "area": "全单位",
     "desc": "消防法第16条年度检测"},
    {"code": "T-O-001", "name": "专项检查任务", "period": "ondemand", "area": "指定区域",
     "desc": "节前/重大活动专项检查"},
]

# ---------- 量化规则（8 条，速查 reference /quant） ----------
QUANT_RULES = [
    {"name": "疏散门", "std": "净宽不应小于 1.4m", "measure": "用卷尺测量门洞净宽",
     "basis": "GB 55037-2022", "judge": "净宽 ≥ 1.4m 为合格"},
    {"name": "疏散距离", "std": "敞开式电信机房任一点至最近安全出口直线距离 ≤ 40m",
     "measure": "现场目测/图纸量取", "basis": "YD 5002", "judge": "≤ 40m 为合格"},
    {"name": "灭火器配置", "std": "单具灭火器最小配置级别 2A，保护距离 ≤ 20m",
     "measure": "查看灭火器铭牌+测量距离", "basis": "GB 50140", "judge": "级别与距离均满足为合格"},
    {"name": "应急照明", "std": "疏散走道地面最低水平照度 ≥ 1.0 lx，备用电源连续供电 ≥ 30min",
     "measure": "照度计/查看备用电源", "basis": "GB 51309", "judge": "照度与时间均满足为合格"},
    {"name": "防火间距", "std": "高层建筑之间 ≥ 13m，多层 ≥ 6m",
     "measure": "现场目测/图纸量取", "basis": "GB 50016", "judge": "≥ 规定值 为合格"},
    {"name": "消防通道", "std": "消防车通道净宽 ≥ 4m，转弯半径 ≥ 12m",
     "measure": "卷尺测量", "basis": "GB 50016", "judge": "净宽 ≥ 4m 为合格"},
    {"name": "喷头间距", "std": "标准喷头间距 2.4m ~ 3.6m",
     "measure": "卷尺测量相邻喷头距离", "basis": "GB 50261", "judge": "在范围内为合格"},
    {"name": "探测器间距", "std": "点型感烟探测器安装间距 ≤ 15m",
     "measure": "卷尺测量", "basis": "GB 50116", "judge": "≤ 15m 为合格"},
]

# ---------- 验收模板（11 类） ----------
ACCEPT_POINTS = [
    {"name": "建筑防火", "points": ["防火分隔完好", "防火封堵到位", "防火门等级正确", "安全出口数量充足"]},
    {"name": "消防给水", "points": ["消防水池水位正常", "稳压泵运行正常", "消防水泵自动启动", "管网压力正常"]},
    {"name": "自动喷水", "points": ["喷头无遮挡", "末端试水正常", "报警阀组正常", "水流指示器灵敏"]},
    {"name": "火灾报警", "points": ["探测器无故障", "控制器联动正常", "手动报警按钮正常", "声光警报正常"]},
    {"name": "防烟排烟", "points": ["风机运行正常", "防火阀动作正常", "排烟口开启正常", "正压送风正常"]},
    {"name": "气体灭火", "points": ["钢瓶压力正常", "喷嘴无堵塞", "手自动开关在自动位", "防护区密闭良好"]},
    {"name": "应急疏散", "points": ["疏散指示完好", "应急照明正常", "疏散通道畅通", "安全出口开启正常"]},
    {"name": "消防电源", "points": ["双路供电正常", "发电机启动正常", "UPS 正常", "消防泵双电源切换正常"]},
    {"name": "消火栓系统", "points": ["栓口压力正常", "水带水枪齐全", "消火栓无遮挡", "水泵接合器正常"]},
    {"name": "灭火器", "points": ["压力表在绿区", "铅封完好", "配置数量充足", "在有效期内"]},
    {"name": "应急广播电话", "points": ["广播分区正常", "音量清晰", "电话通话正常", "声光联动正常"]},
]

# ---------- 台账类型（8 类） ----------
LEDGER_TYPES = ["值班记录", "防火巡查", "防火检查", "消防培训", "灭火演练", "消防设施维保", "隐患整改", "消防档案"]

# ---------- 应急处置卡（emg 页） ----------
EMG_CARDS = [
    {"key": "fire8", "title": "火情处置八步法", "steps": [
        "确认火情：查看报警信息，派人确认", "启动预案：立即报告消防安全责任人",
        "拨 119 报警：说清单位、地址、火势、有无人员被困", "转自动：确认联动在自动位，启动排烟",
        "扑救初起：就近取灭火器/消火栓扑救", "断电疏散：切断非消防电源，引导疏散",
        "接应消防：派人门口接应消防车", "保护现场：火灾扑灭后保护现场，配合调查"]},
    {"key": "gas", "title": "气体灭火区撤离", "steps": [
        "听到声光报警立即撤离防护区", "确认防护区无人后方可喷放",
        "喷放后严禁立即进入（HF 高温分解有腐蚀性）", "必须通风置换、检测合格后方可进入",
        "喷放后检修，恢复手自动开关至自动位"]},
    {"key": "elect", "title": "机房带电灭火", "steps": [
        "带电设备严禁用水、泡沫灭火", "机房只能用二氧化碳或干粉灭火器",
        "优先切断该回路电源后再灭火", "使用二氧化碳时注意防止冻伤"]},
    {"key": "119", "title": "119 报警话术", "steps": [
        "单位名称与详细地址", "起火楼层与具体部位", "火势大小、有无蔓延",
        "有无人员被困", "燃烧物性质（电气/油类/一般）", "报警人姓名与联系电话"]},
]

# ---------- 设备操作卡（15 类，equip/guide） ----------
EQUIP_GUIDES = [
    {"key": "controller", "name": "火灾报警控制器", "normal": "无火警无故障无屏蔽，联动在自动位",
     "operate": ["查看火警信息并派人确认", "确认后按流程处置/复位", "消音≠处理，报警信息需处置"],
     "forbid": ["严禁长期屏蔽故障点", "严禁只消音不处理", "严禁擅改联动逻辑"],
     "params": "主电/备电正常，故障率 0"},
    {"key": "smoke", "name": "感烟/感温探测器", "normal": "指示灯每 10-30s 闪亮一次",
     "operate": ["定期清洁防积灰", "抽检响应正常"], "forbid": ["严禁遮挡探测器"],
     "params": "安装间距 ≤ 15m"},
    {"key": "manual", "name": "手动报警按钮", "normal": "无损坏，复位正常",
     "operate": ["测试需通知控制室", "测试后复位"], "forbid": ["严禁误触误报"], "params": ""},
    {"key": "hydrant", "name": "室内消火栓", "normal": "栓口压力正常，配件齐全",
     "operate": ["开阀放水测试", "检查水带水枪"], "forbid": ["严禁遮挡消火栓"], "params": "栓口动压 0.35MPa"},
    {"key": "sprinkler", "name": "自动喷水灭火系统", "normal": "报警阀组压力正常",
     "operate": ["末端试水测试", "观察压力变化"], "forbid": ["严禁误关信号阀"], "params": ""},
    {"key": "fm200", "name": "七氟丙烷气体灭火", "normal": "手自动开关在自动位，钢瓶压力正常",
     "operate": ["检查压力表", "确认保护区无人"], "forbid": ["喷放后严禁立即进入", "严禁长期置于手动"],
     "params": "通信机房设计浓度 8%，喷放 ≤ 8s，浸渍 5min"},
    {"key": "ig541", "name": "IG541 气体灭火", "normal": "钢瓶压力按温度-压力对照正常",
     "operate": ["检查压力（需换算）", "确认保护区密闭"], "forbid": ["喷放后缺氧严禁进入"],
     "params": "20℃ 储存约 15MPa，喷放 48-60s"},
    {"key": "portable", "name": "手提式灭火器", "normal": "压力表在绿区，铅封完好",
     "operate": ["拔销、对准火焰根部、压把"], "forbid": ["带电设备严禁用水/泡沫"],
     "params": "在有效期内，压力绿区"},
    {"key": "smoke-ctrl", "name": "防排烟系统", "normal": "风机运行正常",
     "operate": ["手动启动风机", "检查排烟口"], "forbid": ["严禁关闭风机电源"], "params": ""},
    {"key": "shutter", "name": "防火卷帘/防火门", "normal": "卷帘升降正常，防火门自动关闭",
     "operate": ["测试卷帘三种控制方式", "检查防火门烟密闭"],
     "forbid": ["严禁用灭火器楔住防火门"], "params": ""},
    {"key": "emergency", "name": "应急照明/疏散指示", "normal": "灯具完好，自动点亮",
     "operate": ["断电测试应急点亮", "检查指示方向"], "forbid": [], "params": "备用电源 ≥ 30min"},
    {"key": "lift", "name": "消防电梯", "normal": "迫降功能正常",
     "operate": ["测试迫降至首层", "测试开门"], "forbid": ["火灾时严禁乘用非消防电梯"], "params": ""},
    {"key": "water", "name": "消防供水设施", "normal": "水池水位正常，稳压泵正常",
     "operate": ["检查水位", "测试稳压泵"], "forbid": [], "params": ""},
    {"key": "broadcast", "name": "应急广播/消防电话", "normal": "分区广播正常，电话通话清晰",
     "operate": ["测试广播", "测试消防电话"], "forbid": [], "params": ""},
    {"key": "lpg", "name": "气体灭火控制器与紧急启停", "normal": "无报警，紧急启停按钮完好",
     "operate": ["延时阶段可紧急停止", "喷放开始后无法停止"],
     "forbid": ["喷放后严禁立即进入"], "params": "延时 ≤ 30s"},
]

# ---------- 抽考题库（22 道判断题，quiz） ----------
QUIZ_QUESTIONS = [
    {"q": "火灾报警控制器处于手动状态时，联动设备也能自动启动。", "ans": False, "explain": "手动状态下联动设备不自动启动，应置于自动位。"},
    {"q": "气体灭火系统检修后应恢复至自动状态。", "ans": True, "explain": "检修后必须恢复自动，防误喷的同时确保可靠联动。"},
    {"q": "机房内可以用水扑救带电设备火灾。", "ans": False, "explain": "带电设备严禁用水，应用二氧化碳或干粉灭火器。"},
    {"q": "防火门可以用灭火器楔住使其常开。", "ans": False, "explain": "常闭防火门应保持关闭，严禁楔住常开。"},
    {"q": "长期屏蔽故障点等于停用消防设施，属违规。", "ans": True, "explain": "屏蔽故障点违反《消防法》第28条、第60条。"},
    {"q": "消音操作即代表报警已处理。", "ans": False, "explain": "消音不等于处理，报警信息仍需确认处置。"},
    {"q": "交直流电源线与信号线可以混敷。", "ans": False, "explain": "通信机楼要求三线分离，严禁混敷。"},
    {"q": "值班员应每2小时记录一次消防控制室运行情况。", "ans": True, "explain": "GB 25201 要求24h值班、每班≥2人、每2h记录。"},
    {"q": "气体灭火喷放后可以立即进入防护区。", "ans": False, "explain": "喷放后高温分解产生HF，须通风检测合格后才能进入。"},
    {"q": "灭火器压力表指针在红色区域表示压力正常。", "ans": False, "explain": "指针应在绿色区域表示正常。"},
    {"q": "疏散通道可以临时堆放杂物。", "ans": False, "explain": "疏散通道必须保持畅通，严禁堆放杂物。"},
    {"q": "发现火灾应第一时间拨打119。", "ans": True, "explain": "任何人发现火灾都应立即报警。"},
    {"q": "防火巡查时发现隐患应登记上报。", "ans": True, "explain": "发现隐患应及时登记并进入整改流程。"},
    {"q": "消防控制室可以无人值守。", "ans": False, "explain": "消防控制室必须24小时有人值班，每班不少于2人。"},
    {"q": "夜间营业期间可以不进行防火巡查。", "ans": False, "explain": "公众聚集场所营业期间每2小时巡查一次。"},
    {"q": "建筑消防设施应每年至少一次全面检测。", "ans": True, "explain": "《消防法》第16条要求年度检测。"},
    {"q": "灭火和应急疏散演练每半年至少一次。", "ans": True, "explain": "61号令第40条要求重点单位每半年演练一次。"},
    {"q": "擅自使用大功率电器不违规。", "ans": False, "explain": "通信机楼严禁擅自使用大功率电器。"},
    {"q": "机楼内可以吸烟。", "ans": False, "explain": "机楼内禁止吸烟、禁止擅自使用明火。"},
    {"q": "消防救援口净高净宽均应不小于1.0米。", "ans": True, "explain": "GB 55037 第2.2.3条要求。"},
    {"q": "消防控制室值班员无需持证上岗。", "ans": False, "explain": "自动消防系统操作人员必须持证上岗。"},
    {"q": "单位应定期组织员工消防安全培训。", "ans": True, "explain": "61号令第36条要求每年至少一次培训。"},
]

# ---------- 领导十查（spot 十查模式，10 项否决项） ----------
SPOT_TEN = [
    {"name": "消防控制室值班", "check": "24h值班、每班≥2人、持证上岗", "veto": True},
    {"name": "控制器状态", "check": "无故障无屏蔽、联动在自动位", "veto": True},
    {"name": "气体灭火状态", "check": "手自动开关在自动位、钢瓶压力正常", "veto": True},
    {"name": "机房烟火", "check": "严禁烟火、禁放锂电池与易燃品", "veto": True},
    {"name": "蓄电池", "check": "无鼓包、漏液、过温", "veto": True},
    {"name": "三线分离", "check": "交直流电源线与信号线不得混敷", "veto": True},
    {"name": "储油设施", "check": "储油量≤1m³、独立防火分隔", "veto": True},
    {"name": "疏散通道", "check": "安全出口畅通、疏散指示正常", "veto": True},
    {"name": "防火门", "check": "防火门自动关闭、无楔住常开", "veto": True},
    {"name": "动火作业", "check": "审批、持证、监护、随工到位", "veto": True},
]

# 深度检查（十查 + 建筑防火加查 16 项）
SPOT_DEEP_EXTRA = [
    {"name": "防火分隔", "check": "防火墙/隔墙完好，无擅自开洞", "veto": False},
    {"name": "防火封堵", "check": "贯穿孔口封堵到位", "veto": False},
    {"name": "消防车道", "check": "净宽≥4m，畅通", "veto": True},
    {"name": "登高场地", "check": "设置与消防车道配合", "veto": False},
    {"name": "消防救援口", "check": "净高净宽≥1.0m、有标志", "veto": True},
    {"name": "防烟分区", "check": "防烟分区完整", "veto": False},
    {"name": "机械排烟", "check": "三种启动方式正常", "veto": False},
    {"name": "正压送风", "check": "余压正常", "veto": False},
    {"name": "应急照明", "check": "备用电源≥30min", "veto": False},
    {"name": "灭火器", "check": "配置充足、压力正常", "veto": False},
    {"name": "消火栓", "check": "栓口动压0.35MPa", "veto": False},
    {"name": "自动喷水", "check": "末端试水正常", "veto": False},
    {"name": "火灾报警联动", "check": "联动设备全部动作", "veto": True},
    {"name": "消防电源", "check": "双路供电正常", "veto": False},
    {"name": "装修保温", "check": "A级装修、保温完好", "veto": False},
    {"name": "避难层间", "check": "未被挪作他用", "veto": True},
]
