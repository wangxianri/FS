-- ============================================================
-- 消防履责工作台 独立 App · 数据库 Schema
-- 库名: fs_standalone (MySQL, utf8mb4)
-- 版本: V2.0
-- ============================================================

CREATE DATABASE IF NOT EXISTS `fs_standalone` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `fs_standalone`;

-- ------------------------------------------------------------
-- 一、业务表（9 张，结构对齐 EPM fs_* 表）
-- ------------------------------------------------------------

-- 检查标准库（法规 5 要素 / 周期 / 等级 / 否决项 / 整改期限 / 角色）
CREATE TABLE IF NOT EXISTS `fs_check_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `code` VARCHAR(64) NOT NULL DEFAULT '',
  `name` VARCHAR(200) NOT NULL,
  `area` VARCHAR(100) NOT NULL DEFAULT '',          -- 部位/区域
  `how` TEXT,                                       -- 怎么查
  `std` TEXT,                                       -- 合格标准
  `basis` TEXT,                                     -- 法规依据
  `penalty` TEXT,                                   -- 处罚条款
  `fix` TEXT,                                       -- 整改措施
  `period` VARCHAR(32) NOT NULL DEFAULT 'daily',    -- twohour/shift/daily/weekly/monthly/quarterly/halfyear/yearly/ondemand
  `level` VARCHAR(16) NOT NULL DEFAULT 'normal',    -- 风险等级 high/mid/low/normal
  `veto` TINYINT NOT NULL DEFAULT 0,                -- 是否一票否决
  `days` INT NOT NULL DEFAULT 3,                    -- 整改期限(天)
  `role` VARCHAR(32) NOT NULL DEFAULT 'grass',      -- 适用角色
  `sort` INT NOT NULL DEFAULT 0,
  `enabled` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_area` (`area`),
  KEY `idx_period` (`period`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 法规对照库（?area=&q= 搜索）
CREATE TABLE IF NOT EXISTS `fs_law_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `area` VARCHAR(100) NOT NULL DEFAULT '',
  `name` VARCHAR(200) NOT NULL,
  `category` VARCHAR(100) NOT NULL DEFAULT '',      -- 法律/行政法规/部门规章/国家标准/行业标准
  `basis` TEXT,                                     -- 条文原文
  `penalty` TEXT,
  `sort` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_area` (`area`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 随手拍照片（data_url base64）
CREATE TABLE IF NOT EXISTS `fs_photos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL DEFAULT 0,
  `biz_type` VARCHAR(32) NOT NULL DEFAULT '',       -- hazard/inspection
  `biz_id` INT NOT NULL DEFAULT 0,                  -- 关联隐患/巡检 id
  `site_id` VARCHAR(100) NOT NULL DEFAULT '',       -- 点位标识（用于同点位历史归档）
  `data_url` LONGTEXT,                              -- base64
  `caption` VARCHAR(200) NOT NULL DEFAULT '',
  `unit_id` INT NOT NULL DEFAULT 0,                 -- 所属单位
  `building_id` INT NOT NULL DEFAULT 0,             -- 所属楼宇
  `place_id` INT NOT NULL DEFAULT 0,                -- 所属场所
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_biz` (`biz_type`, `biz_id`),
  KEY `idx_site` (`site_id`),
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`),
  KEY `idx_place` (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 履责任务（按 9 类周期自动生成）
CREATE TABLE IF NOT EXISTS `fs_tasks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `code` VARCHAR(64) NOT NULL DEFAULT '',
  `name` VARCHAR(200) NOT NULL,
  `period` VARCHAR(32) NOT NULL DEFAULT 'daily',
  `area` VARCHAR(100) NOT NULL DEFAULT '',
  `unit_id` INT NOT NULL DEFAULT 0,                 -- 所属单位
  `building_id` INT NOT NULL DEFAULT 0,             -- 所属楼宇
  `place_id` INT NOT NULL DEFAULT 0,                -- 所属场所
  `template_id` INT NOT NULL DEFAULT 0,
  `status` VARCHAR(32) NOT NULL DEFAULT 'pending',  -- pending/in_progress/rectifying/done
  `due_date` DATE,
  `completed_at` DATETIME,
  `assigned_to` VARCHAR(100) NOT NULL DEFAULT '',
  `score` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_period` (`period`),
  KEY `idx_status` (`status`),
  KEY `idx_due` (`due_date`),
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`),
  KEY `idx_place` (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 巡检结果明细
CREATE TABLE IF NOT EXISTS `fs_inspections` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `task_id` INT NOT NULL DEFAULT 0,
  `area` VARCHAR(100) NOT NULL DEFAULT '',
  `unit_id` INT NOT NULL DEFAULT 0,                 -- 所属单位
  `building_id` INT NOT NULL DEFAULT 0,             -- 所属楼宇
  `place_id` INT NOT NULL DEFAULT 0,                -- 所属场所
  `results` LONGTEXT,                               -- JSON [{name,result,note}]
  `fail_count` INT NOT NULL DEFAULT 0,
  `result_status` VARCHAR(32) NOT NULL DEFAULT 'done', -- done/rectifying
  `user_id` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_task` (`task_id`),
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`),
  KEY `idx_place` (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 隐患（状态机 + photo_ids）
CREATE TABLE IF NOT EXISTS `fs_hazards` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(200) NOT NULL,
  `area` VARCHAR(100) NOT NULL DEFAULT '',
  `unit_id` INT NOT NULL DEFAULT 0,                 -- 所属单位
  `building_id` INT NOT NULL DEFAULT 0,             -- 所属楼宇
  `place_id` INT NOT NULL DEFAULT 0,                -- 所属场所
  `level` VARCHAR(16) NOT NULL DEFAULT 'mid',       -- high/mid/low
  `desc` TEXT,
  `status` VARCHAR(32) NOT NULL DEFAULT 'open',     -- open/rectifying/rechecked/closed
  `deadline` DATE,
  `reporter_id` INT NOT NULL DEFAULT 0,
  `reporter_name` VARCHAR(100) NOT NULL DEFAULT '',
  `assignee_id` INT NOT NULL DEFAULT 0,
  `assignee_name` VARCHAR(100) NOT NULL DEFAULT '',
  `rectify_note` TEXT,
  `recheck_note` TEXT,
  `close_note` TEXT,
  `photo_ids` TEXT,                                 -- 逗号分隔照片 id
  `closed_at` DATETIME,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_status` (`status`),
  KEY `idx_level` (`level`),
  KEY `idx_area` (`area`),
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`),
  KEY `idx_place` (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 消防台账（8 类）
CREATE TABLE IF NOT EXISTS `fs_ledger` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `type` VARCHAR(64) NOT NULL DEFAULT '',
  `title` VARCHAR(200) NOT NULL,
  `content` TEXT,
  `unit_id` INT NOT NULL DEFAULT 0,                 -- 所属单位
  `building_id` INT NOT NULL DEFAULT 0,             -- 所属楼宇
  `place_id` INT NOT NULL DEFAULT 0,                -- 所属场所
  `user_id` INT NOT NULL DEFAULT 0,
  `user_name` VARCHAR(100) NOT NULL DEFAULT '',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_type` (`type`),
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`),
  KEY `idx_place` (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 消防验收记录
CREATE TABLE IF NOT EXISTS `fs_acceptance` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `project` VARCHAR(200) NOT NULL,
  `result` VARCHAR(32) NOT NULL DEFAULT 'pass',     -- pass/fail/pending
  `note` TEXT,
  `unit_id` INT NOT NULL DEFAULT 0,                 -- 所属单位
  `building_id` INT NOT NULL DEFAULT 0,             -- 所属楼宇
  `place_id` INT NOT NULL DEFAULT 0,                -- 所属场所
  `template_id` INT NOT NULL DEFAULT 0,
  `user_id` INT NOT NULL DEFAULT 0,
  `user_name` VARCHAR(100) NOT NULL DEFAULT '',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_project` (`project`),
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`),
  KEY `idx_place` (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 元数据/版本
CREATE TABLE IF NOT EXISTS `fs_meta` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `meta_key` VARCHAR(100) NOT NULL,
  `meta_value` TEXT,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_key` (`meta_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 二、账号表（4 张，V2.0 新增）
-- ------------------------------------------------------------

-- 独立账号主表
CREATE TABLE IF NOT EXISTS `fs_app_users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `phone` VARCHAR(20) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL DEFAULT '',
  `name` VARCHAR(100) NOT NULL DEFAULT '',
  `role` VARCHAR(32) NOT NULL DEFAULT 'grass',       -- grass/mid/top/accept/admin
  `unit_id` INT NOT NULL DEFAULT 0,                  -- 所属单位（系统管理员可为 0）
  `avatar` VARCHAR(500) NOT NULL DEFAULT '',
  `status` TINYINT NOT NULL DEFAULT 1,              -- 1 启用 / 0 停用
  `token_version` INT NOT NULL DEFAULT 0,           -- 停用/改密/登出即时失效
  `last_login_at` DATETIME,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 微信 openid 绑定关系
CREATE TABLE IF NOT EXISTS `fs_wechat_bind` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `openid` VARCHAR(128) NOT NULL,
  `unionid` VARCHAR(128) DEFAULT '',
  `bind_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login_at` DATETIME,
  UNIQUE KEY `uk_openid` (`openid`),
  KEY `idx_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 短信/验证码记录
CREATE TABLE IF NOT EXISTS `fs_sms_codes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `phone` VARCHAR(20) NOT NULL,
  `code_hash` VARCHAR(255) NOT NULL,
  `purpose` VARCHAR(32) NOT NULL DEFAULT 'register',-- register/forgot/bind
  `expires_at` DATETIME NOT NULL,
  `used` TINYINT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 角色-模块权限配置
CREATE TABLE IF NOT EXISTS `fs_roles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `role_key` VARCHAR(32) NOT NULL,
  `name` VARCHAR(64) NOT NULL,
  `modules` TEXT,                                   -- JSON 模块权限数组
  `is_system` TINYINT NOT NULL DEFAULT 1,
  UNIQUE KEY `uk_role` (`role_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 三、增强表（P1/P2，可选）
-- ------------------------------------------------------------

-- 领导快检结论
CREATE TABLE IF NOT EXISTS `fs_spot_checks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `mode` VARCHAR(32) NOT NULL DEFAULT 'ten',        -- ten/deep
  `site_id` VARCHAR(100) NOT NULL DEFAULT '',
  `site_name` VARCHAR(200) NOT NULL DEFAULT '',
  `unit_id` INT NOT NULL DEFAULT 0,                 -- 所属单位
  `building_id` INT NOT NULL DEFAULT 0,             -- 所属楼宇
  `place_id` INT NOT NULL DEFAULT 0,                -- 所属场所
  `items` LONGTEXT,                                 -- JSON [{name,pass,note}]
  `pass_count` INT NOT NULL DEFAULT 0,
  `fail_count` INT NOT NULL DEFAULT 0,
  `result` VARCHAR(64) NOT NULL DEFAULT '',
  `conclusion` TEXT,
  `user_id` INT NOT NULL DEFAULT 0,
  `user_name` VARCHAR(100) NOT NULL DEFAULT '',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_site` (`site_id`),
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`),
  KEY `idx_place` (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 隐患督办派单
CREATE TABLE IF NOT EXISTS `fs_supervise_tasks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `hazard_id` INT NOT NULL,
  `assignee_id` INT NOT NULL DEFAULT 0,
  `assignee_name` VARCHAR(100) NOT NULL DEFAULT '',
  `deadline` DATE,
  `note` TEXT,
  `status` VARCHAR(32) NOT NULL DEFAULT 'assigned', -- assigned/in_progress/done
  `creator_id` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_hazard` (`hazard_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 抽考成绩
CREATE TABLE IF NOT EXISTS `fs_quizzes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `quizzer_id` INT NOT NULL DEFAULT 0,              -- 出题人(领导/中层)
  `employee_name` VARCHAR(100) NOT NULL DEFAULT '',
  `unit_id` INT NOT NULL DEFAULT 0,                 -- 所属单位
  `building_id` INT NOT NULL DEFAULT 0,             -- 所属楼宇
  `place_id` INT NOT NULL DEFAULT 0,                -- 所属场所
  `questions` LONGTEXT,                             -- JSON 题目与用户答案
  `score` INT NOT NULL DEFAULT 0,
  `total` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`),
  KEY `idx_place` (`place_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 离线同步日志（幂等去重）
CREATE TABLE IF NOT EXISTS `fs_offline_sync_log` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `client_id` VARCHAR(64) NOT NULL,
  `action` VARCHAR(64) NOT NULL,
  `payload` LONGTEXT,
  `user_id` INT NOT NULL DEFAULT 0,
  `status` VARCHAR(32) NOT NULL DEFAULT 'applied',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_client` (`client_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 单位（消防履责单位，三级层级：省公司/市公司/区县公司）
CREATE TABLE IF NOT EXISTS `fs_units` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(200) NOT NULL,
  `code` VARCHAR(64) NOT NULL DEFAULT '',
  `parent_id` INT NOT NULL DEFAULT 0,              -- 上级单位ID（0=顶级，即省公司）
  `level` TINYINT NOT NULL DEFAULT 1,               -- 层级 1=省公司 2=市公司 3=区县公司
  `contact` VARCHAR(100) NOT NULL DEFAULT '',
  `phone` VARCHAR(30) NOT NULL DEFAULT '',
  `address` VARCHAR(300) NOT NULL DEFAULT '',
  `remark` TEXT,
  `enabled` TINYINT NOT NULL DEFAULT 1,
  `sort` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_code` (`code`),
  KEY `idx_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 楼宇（单位下建筑）
CREATE TABLE IF NOT EXISTS `fs_buildings` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `unit_id` INT NOT NULL DEFAULT 0,
  `name` VARCHAR(200) NOT NULL,
  `code` VARCHAR(64) NOT NULL DEFAULT '',
  `floors` INT NOT NULL DEFAULT 0,
  `address` VARCHAR(300) NOT NULL DEFAULT '',
  `remark` TEXT,
  `enabled` TINYINT NOT NULL DEFAULT 1,
  `sort` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_unit` (`unit_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 场所（楼宇内检查场所/部位）
CREATE TABLE IF NOT EXISTS `fs_places` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `unit_id` INT NOT NULL DEFAULT 0,
  `building_id` INT NOT NULL DEFAULT 0,
  `name` VARCHAR(200) NOT NULL,
  `code` VARCHAR(64) NOT NULL DEFAULT '',
  `floor` VARCHAR(64) NOT NULL DEFAULT '',
  `type` VARCHAR(64) NOT NULL DEFAULT '',
  `remark` TEXT,
  `enabled` TINYINT NOT NULL DEFAULT 1,
  `sort` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 维保与报修（故障闭环：登记→维修中→待验收→已闭环）
CREATE TABLE IF NOT EXISTS `fs_repairs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `code` VARCHAR(64) NOT NULL DEFAULT '',
  `device` VARCHAR(200) NOT NULL,
  `location` VARCHAR(200) NOT NULL DEFAULT '',
  `unit_id` INT NOT NULL DEFAULT 0,
  `building_id` INT NOT NULL DEFAULT 0,
  `place_id` INT NOT NULL DEFAULT 0,
  `fault_desc` TEXT,
  `status` VARCHAR(32) NOT NULL DEFAULT 'open',      -- open/repairing/checking/closed
  `repair_note` TEXT,
  `check_note` TEXT,
  `deadline` DATE,
  `reporter_id` INT NOT NULL DEFAULT 0,
  `reporter_name` VARCHAR(100) NOT NULL DEFAULT '',
  `assignee_name` VARCHAR(100) NOT NULL DEFAULT '',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_status` (`status`),
  KEY `idx_unit` (`unit_id`),
  KEY `idx_building` (`building_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 任务下发（节前/重大活动专项任务，一键下发到单位）
CREATE TABLE IF NOT EXISTS `fs_notices` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(200) NOT NULL,
  `content` TEXT,
  `unit_id` INT NOT NULL DEFAULT 0,                  -- 下发范围（0=全部单位）
  `deadline` DATE,
  `status` VARCHAR(32) NOT NULL DEFAULT 'active',    -- active/done/cancelled
  `creator_id` INT NOT NULL DEFAULT 0,
  `creator_name` VARCHAR(100) NOT NULL DEFAULT '',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_status` (`status`),
  KEY `idx_unit` (`unit_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
