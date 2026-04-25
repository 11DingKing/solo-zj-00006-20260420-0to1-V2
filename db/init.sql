-- 食谱管理平台数据库初始化脚本
-- 数据库版本：MySQL 8.0

-- 创建数据库
CREATE DATABASE IF NOT EXISTS recipe_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE recipe_db;

-- 分类表
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '分类名称',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='食谱分类表';

-- 难度表
CREATE TABLE IF NOT EXISTS difficulties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '难度名称',
    level INT NOT NULL COMMENT '难度级别',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='难度表';

-- 单位表
CREATE TABLE IF NOT EXISTS units (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '单位名称',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='单位表';

-- 食谱表
CREATE TABLE IF NOT EXISTS recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '菜名',
    category_id INT NOT NULL COMMENT '分类ID',
    difficulty_id INT NOT NULL COMMENT '难度ID',
    cooking_time INT NOT NULL COMMENT '烹饪时间（分钟）',
    cover_url VARCHAR(500) COMMENT '封面图URL',
    steps TEXT COMMENT '步骤描述（JSON格式存储多步骤）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (difficulty_id) REFERENCES difficulties(id),
    INDEX idx_category (category_id),
    INDEX idx_difficulty (difficulty_id),
    INDEX idx_cooking_time (cooking_time),
    INDEX idx_name (name(50))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='食谱表';

-- 食材表
CREATE TABLE IF NOT EXISTS ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT NOT NULL COMMENT '食谱ID',
    name VARCHAR(100) NOT NULL COMMENT '食材名称',
    amount DECIMAL(10,2) NOT NULL COMMENT '用量',
    unit_id INT NOT NULL COMMENT '单位ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES units(id),
    INDEX idx_recipe (recipe_id),
    INDEX idx_name (name(50))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='食材表';

-- 本周菜单表
CREATE TABLE IF NOT EXISTS weekly_menu (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT NOT NULL COMMENT '食谱ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE KEY uk_recipe (recipe_id),
    INDEX idx_recipe (recipe_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='本周菜单表';

-- 插入初始分类数据
INSERT INTO categories (name) VALUES 
('中餐'),
('西餐'),
('日料'),
('甜点'),
('饮品'),
('素食'),
('家常菜'),
('快手菜');

-- 插入初始难度数据
INSERT INTO difficulties (name, level) VALUES 
('简单', 1),
('中等', 2),
('困难', 3);

-- 插入初始单位数据
INSERT INTO units (name) VALUES 
('克'),
('毫升'),
('个'),
('勺'),
('茶匙'),
('汤匙'),
('片'),
('块'),
('根'),
('适量'),
('少许');
