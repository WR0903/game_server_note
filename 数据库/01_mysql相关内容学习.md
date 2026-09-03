---
title: mysql相关内容学习
category: 数据库
created_at: 2026-04-26 12:31:09
view_count: 6
---

# MySQL 实用指南

## 目录
1. [概述与连接](#1-概述与连接)
2. [数据库操作](#2-数据库操作)
3. [表操作](#3-表操作)
4. [数据库三大范式](#4-数据库三大范式)
5. [数据 CRUD](#5-数据-crud)
   - [插入](#51-插入-insert)
   - [查询](#52-查询-select)
   - [更新](#53-更新-update)
   - [删除](#54-删除-delete)
6. [索引](#6-索引)
7. [事务与锁](#7-事务与锁)
8. [MVCC 多版本并发控制](#8-mvcc-多版本并发控制)
9. [MySQL 架构](#9-mysql-架构)
10. [视图、存储过程与触发器](#10-视图存储过程与触发器)
11. [存储引擎详解](#11-存储引擎详解)
12. [主从复制](#12-主从复制)
13. [分库分表与大表优化](#13-分库分表与大表优化)
14. [分区表](#14-分区表)
15. [常用命令速查](#15-常用命令速查)

---

## 1. 概述与连接

### 基本概念

| 概念 | 说明 |
|---|---|
| **数据库 Database** | 表的容器 |
| **表 Table** | 行列结构存储数据 |
| **列 Column** | 字段，有明确数据类型 |
| **行 Row** | 一条记录 |
| **索引 Index** | 加速查询的数据结构 |
| **主键 Primary Key** | 唯一标识每行 |
| **外键 Foreign Key** | 表间关联约束 |

### 连接方式

```bash
# 命令行连接
mysql -h 127.0.0.1 -P 3306 -u root -p

# 指定数据库
mysql -h 127.0.0.1 -u root -p mydb

# 执行 SQL 文件
mysql -u root -p mydb < backup.sql

# 查看连接数
mysql -u root -p -e "SHOW PROCESSLIST"
```

#### 编程语言连接示例

```python
# Python (pymysql)
import pymysql

conn = pymysql.connect(
    host='127.0.0.1', port=3306,
    user='root', password='password',
    database='mydb', charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
result = cursor.fetchone()
conn.close()
```

```python
# Python (SQLAlchemy ORM)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    'mysql+pymysql://root:password@127.0.0.1:3306/mydb?charset=utf8mb4',
    pool_size=10, max_overflow=20, pool_recycle=3600
)
Session = sessionmaker(bind=engine)
session = Session()
```

```go
// Go (go-sql-driver)
import (
    "database/sql"
    _ "github.com/go-sql-driver/mysql"
)

db, err := sql.Open("mysql", "root:password@tcp(127.0.0.1:3306)/mydb?charset=utf8mb4&parseTime=true")
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(5)
db.SetConnMaxLifetime(5 * time.Minute)
defer db.Close()

rows, err := db.Query("SELECT id, name FROM users WHERE age > ?", 25)
```

```javascript
// Node.js (mysql2)
const mysql = require('mysql2/promise');

const pool = mysql.createPool({
    host: '127.0.0.1',
    port: 3306,
    user: 'root',
    password: 'password',
    database: 'mydb',
    charset: 'utf8mb4',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

const [rows] = await pool.execute('SELECT * FROM users WHERE id = ?', [1]);
```

---

## 2. 数据库操作

```sql
-- 查看所有数据库
SHOW DATABASES;

-- 创建数据库
CREATE DATABASE IF NOT EXISTS mydb
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- 查看建库语句
SHOW CREATE DATABASE mydb;

-- 切换数据库
USE mydb;

-- 查看当前数据库
SELECT DATABASE();

-- 修改数据库字符集
ALTER DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- 删除数据库
DROP DATABASE IF EXISTS mydb;
```

### 字符集与排序规则

| 字符集 | 排序规则 | 说明 |
|---|---|---|
| `utf8mb4` | `utf8mb4_unicode_ci` | 完整 Unicode 支持（推荐，支持 emoji） |
| `utf8mb4` | `utf8mb4_general_ci` | 通用排序，性能略优于 unicode |
| `utf8mb4` | `utf8mb4_0900_ai_ci` | MySQL 8.0 默认，不区分重音 |
| `utf8` | `utf8_general_ci` | ⚠️ 不支持 4 字节字符（emoji），已过时 |

---

## 3. 表操作

### 3.1 数据类型速查

**数值类型：**

| 类型 | 范围 | 说明 |
|---|---|---|
| `TINYINT` | -128 ~ 127 | 1 字节 |
| `SMALLINT` | -32768 ~ 32767 | 2 字节 |
| `INT / INTEGER` | -2^31 ~ 2^31-1 | 4 字节，最常用 |
| `BIGINT` | -2^63 ~ 2^63-1 | 8 字节 |
| `FLOAT` | 单精度 | 4 字节 |
| `DOUBLE` | 双精度 | 8 字节 |
| `DECIMAL(M,D)` | 定点数 | 金融计算推荐 |

**字符串类型：**

| 类型 | 最大长度 | 说明 |
|---|---|---|
| `CHAR(N)` | 255 | 定长，短字符串 |
| `VARCHAR(N)` | 65535 | 变长，常用 |
| `TEXT` | 65535 | 长文本 |
| `MEDIUMTEXT` | 16MB | |
| `LONGTEXT` | 4GB | |

**日期时间类型：**

| 类型 | 格式 | 说明 |
|---|---|---|
| `DATE` | YYYY-MM-DD | 日期 |
| `TIME` | HH:MM:SS | 时间 |
| `DATETIME` | YYYY-MM-DD HH:MM:SS | 日期时间（常用）|
| `TIMESTAMP` | 1970~2038 | 自动时区转换 |

### 3.2 创建表

```sql
CREATE TABLE users (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    username    VARCHAR(50)     NOT NULL COMMENT '用户名',
    email       VARCHAR(100)    NOT NULL COMMENT '邮箱',
    password    VARCHAR(255)    NOT NULL COMMENT '密码哈希',
    age         TINYINT UNSIGNED DEFAULT 0 COMMENT '年龄',
    status      ENUM('active','inactive','banned') DEFAULT 'active' COMMENT '状态',
    balance     DECIMAL(12,2)   DEFAULT 0.00 COMMENT '余额',
    avatar_url  VARCHAR(500)    DEFAULT NULL COMMENT '头像地址',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    KEY idx_status (status),
    KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

### 3.3 修改表结构

```sql
-- 添加列
ALTER TABLE users ADD COLUMN phone VARCHAR(20) DEFAULT NULL COMMENT '手机号' AFTER email;

-- 删除列
ALTER TABLE users DROP COLUMN avatar_url;

-- 修改列类型
ALTER TABLE users MODIFY COLUMN age SMALLINT UNSIGNED DEFAULT 0;

-- 重命名列（MySQL 8.0+）
ALTER TABLE users RENAME COLUMN username TO nickname;

-- 添加索引
ALTER TABLE users ADD INDEX idx_phone (phone);
ALTER TABLE users ADD UNIQUE KEY uk_phone (phone);
ALTER TABLE users ADD FULLTEXT INDEX ft_bio (bio);

-- 删除索引
ALTER TABLE users DROP INDEX idx_phone;

-- 添加外键
ALTER TABLE orders ADD CONSTRAINT fk_user_id
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE;

-- 删除外键
ALTER TABLE orders DROP FOREIGN KEY fk_user_id;

-- 重命名表
RENAME TABLE users TO accounts;
ALTER TABLE accounts RENAME TO users;
```

### 3.4 查看表信息

```sql
-- 查看所有表
SHOW TABLES;

-- 查看表结构
DESC users;
DESCRIBE users;
SHOW COLUMNS FROM users;

-- 查看建表语句
SHOW CREATE TABLE users;

-- 查看索引
SHOW INDEX FROM users;

-- 查看表状态（含引擎、行数、大小等）
SHOW TABLE STATUS LIKE 'users';
SHOW TABLE STATUS FROM mydb WHERE Name = 'users';

-- 查看分区
SELECT * FROM information_schema.partitions
WHERE table_schema = 'mydb' AND table_name = 'users';
```

---

## 4. 数据库三大范式

### 4.1 第一范式 (1NF)

**确保每列保持原子性，不可再分。**

❌ 反例：`userInfo` 字段为 `'广东省10086'`，字段包含两个信息。  
✅ 正例：拆分为 `address: '广东省'` 和 `phone: '10086'` 两个字段。

### 4.2 第二范式 (2NF)

满足 1NF 的前提下，**非主键列必须完全依赖于主键**，而不能只依赖于主键的一部分（针对复合主键）。

> 如果主键是单列，且满足 1NF，则自动满足 2NF。

**反例**：选课关系表 `student_course(student_no, student_name, age, course_name, grade, credit)`，主键为 `(student_no, course_name)`。

- `credit`（学分）仅依赖于 `course_name`，不依赖 `student_no`
- `student_name`, `age` 仅依赖于 `student_no`，不依赖 `course_name`
- 问题：数据冗余（学生选 N 门课，姓名年龄重复 N 次）、插入异常（无法单独新增课程）

**正例**：拆分为三张表：
- `student(student_no, student_name, age)`
- `course(course_name, credit)`
- `student_course(student_no, course_name, grade)`

### 4.3 第三范式 (3NF)

满足 2NF 的前提下，**非主键列必须直接依赖于主键**，不能存在传递依赖。

> 即不能存在：非主键列 A 依赖非主键列 B，而 B 依赖主键。

**反例**：学生表 `student(student_no, student_name, age, academy_id, academy_phone)`，主键为 `student_no`。

- `academy_phone` 依赖于 `academy_id`，而 `academy_id` 依赖于 `student_no`
- 存在传递依赖：`student_no → academy_id → academy_phone`

**正例**：拆分为两张表：
- `student(student_no, student_name, age, academy_id)`
- `academy(academy_id, academy_phone)`

### 4.4 2NF 与 3NF 的区别

| 范式 | 核心问题 | 判断依据 |
|---|---|---|
| **2NF** | 非主键列是否**部分依赖**于主键 | 是否存在列只依赖主键的一部分 |
| **3NF** | 非主键列是否**间接依赖**于主键 | 是否存在传递依赖关系 |

> **实际建议**：范式化减少冗余，但过度范式化会导致大量 JOIN。在性能敏感场景，可以适当反范式化（冗余一些字段避免 JOIN）。

---

## 5. 数据 CRUD

### 5.1 插入 (INSERT)

```sql
-- 插入单条
INSERT INTO users (username, email, password, age, status)
VALUES ('张三', 'zhangsan@example.com', 'hash123', 28, 'active');

-- 插入多条
INSERT INTO users (username, email, password, age) VALUES
    ('李四', 'lisi@example.com',   'hash456', 32),
    ('王五', 'wangwu@example.com', 'hash789', 25),
    ('赵六', 'zhaoliu@example.com','hash012', 35);

-- 从查询插入
INSERT INTO active_users (user_id, username, email)
SELECT id, username, email FROM users WHERE status = 'active';

-- 忽略重复（主键/唯一键冲突时跳过）
INSERT IGNORE INTO users (id, username, email) VALUES (1, '重复', 'dup@example.com');

-- 存在则更新（ON DUPLICATE KEY UPDATE）
INSERT INTO users (id, username, email, login_count)
VALUES (1, '张三', 'zhangsan@example.com', 1)
ON DUPLICATE KEY UPDATE
    login_count = login_count + 1,
    updated_at = NOW();

-- 批量插入优化
INSERT INTO logs (user_id, action, created_at) VALUES
    (1, 'login',  NOW()),
    (2, 'logout', NOW()),
    (3, 'view',   NOW());  -- 批量比逐条插入快数十倍
```

### 5.2 查询 (SELECT)

#### 基本查询

```sql
-- 查询全部
SELECT * FROM users;

-- 选择特定列
SELECT id, username, email FROM users;

-- 去重
SELECT DISTINCT status FROM users;

-- 别名
SELECT id AS user_id, username AS name FROM users;

-- LIMIT 分页
SELECT * FROM users ORDER BY id DESC LIMIT 10 OFFSET 20;
-- MySQL 8.0 行号
SELECT * FROM users ORDER BY id DESC LIMIT 20, 10;
```

#### WHERE 条件

```sql
-- 比较
SELECT * FROM users WHERE age > 25;
SELECT * FROM users WHERE age >= 18 AND age <= 35;
SELECT * FROM users WHERE age BETWEEN 18 AND 35;
SELECT * FROM users WHERE status != 'banned';

-- 列表匹配
SELECT * FROM users WHERE status IN ('active', 'inactive');
SELECT * FROM users WHERE id NOT IN (1, 2, 3);

-- NULL 判断
SELECT * FROM users WHERE avatar_url IS NULL;
SELECT * FROM users WHERE avatar_url IS NOT NULL;

-- 模糊匹配
SELECT * FROM users WHERE username LIKE '张%';     -- 以"张"开头
SELECT * FROM users WHERE username LIKE '%三';      -- 以"三"结尾
SELECT * FROM users WHERE email LIKE '%@gmail.com';-- 包含
SELECT * FROM users WHERE username LIKE '张_';      -- 张 + 单个字符
```

#### 正则表达式

```sql
SELECT * FROM users WHERE username REGEXP '^张';            -- 以张开头
SELECT * FROM users WHERE email REGEXP '^[a-z]+@gmail\\.com$'; -- Gmail 邮箱
SELECT * FROM users WHERE username REGEXP BINARY 'Zhang';   -- 大小写敏感
```

#### 排序与分页

```sql
-- 单字段排序
SELECT * FROM users ORDER BY age DESC;
SELECT * FROM users ORDER BY created_at ASC;

-- 多字段排序
SELECT * FROM users ORDER BY status ASC, age DESC;

-- 分页
SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 0;  -- 第 1 页
SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 10; -- 第 2 页

-- 高效分页（避免大 OFFSET）
SELECT * FROM users WHERE id > 1000 ORDER BY id LIMIT 10;
```

#### 聚合函数

```sql
-- 统计
SELECT COUNT(*) FROM users;
SELECT COUNT(DISTINCT status) FROM users;
SELECT COUNT(avatar_url) FROM users;  -- 非 NULL 计数

-- 求和、平均、最大、最小
SELECT
    SUM(balance)        AS total_balance,
    AVG(age)            AS avg_age,
    MAX(age)            AS max_age,
    MIN(age)            AS min_age,
    STDDEV(age)         AS std_age   -- 标准差
FROM users WHERE status = 'active';
```

#### 分组查询

```sql
-- 基本分组
SELECT status, COUNT(*) AS cnt
FROM users
GROUP BY status;

-- 带条件分组
SELECT status, COUNT(*) AS cnt, AVG(age) AS avg_age
FROM users
WHERE age >= 18
GROUP BY status
HAVING cnt > 5       -- 分组后过滤
ORDER BY cnt DESC;

-- WHERE vs HAVING
-- WHERE：分组前过滤行
-- HAVING：分组后过滤组
```

#### 子查询

```sql
-- 标量子查询（返回单个值）
SELECT username, (SELECT COUNT(*) FROM orders WHERE user_id = users.id) AS order_count
FROM users;

-- IN 子查询
SELECT * FROM users
WHERE id IN (SELECT DISTINCT user_id FROM orders WHERE amount > 100);

-- EXISTS 子查询
SELECT * FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);

-- FROM 子查询（派生表）
SELECT avg_age, COUNT(*) FROM (
    SELECT status, AVG(age) AS avg_age
    FROM users
    GROUP BY status
) AS t
WHERE avg_age > 25;
```

#### 连接查询 (JOIN)

```sql
-- INNER JOIN：返回两表匹配的行
SELECT u.username, o.order_no, o.amount, o.created_at
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.amount > 100;

-- LEFT JOIN：左表全保留，右表无匹配填 NULL
SELECT u.username, COUNT(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;

-- RIGHT JOIN：右表全保留
SELECT u.username, o.order_no
FROM users u
RIGHT JOIN orders o ON u.id = o.user_id;

-- CROSS JOIN：笛卡尔积
SELECT * FROM users CROSS JOIN roles;

-- 多表连接
SELECT u.username, o.order_no, p.product_name, oi.quantity
FROM users u
JOIN orders o       ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p     ON oi.product_id = p.id;

-- 自连接
SELECT a.username AS employee, b.username AS manager
FROM users a
LEFT JOIN users b ON a.manager_id = b.id;
```

#### 联合查询 (UNION)

```sql
-- UNION：合并结果集并去重
SELECT username FROM users WHERE status = 'active'
UNION
SELECT username FROM admins;

-- UNION ALL：合并结果集不去重（更快）
SELECT username FROM users WHERE status = 'active'
UNION ALL
SELECT username FROM inactive_users;
```

#### 窗口函数 (MySQL 8.0+)

```sql
-- ROW_NUMBER：行号
SELECT username, age,
    ROW_NUMBER() OVER (ORDER BY age DESC) AS rank_num
FROM users;

-- RANK / DENSE_RANK：排名
SELECT username, age,
    RANK()       OVER (ORDER BY age DESC) AS rank1,  -- 有间隔
    DENSE_RANK() OVER (ORDER BY age DESC) AS rank2   -- 无间隔
FROM users;

-- 分区内排名
SELECT username, status, age,
    ROW_NUMBER() OVER (PARTITION BY status ORDER BY age DESC) AS status_rank
FROM users;

-- 累计统计
SELECT id, amount,
    SUM(amount) OVER (ORDER BY created_at) AS running_total
FROM orders;

-- 移动平均
SELECT created_at, amount,
    AVG(amount) OVER (ORDER BY created_at ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg_7
FROM orders;

-- LEAD / LAG：前后行对比
SELECT created_at, amount,
    LAG(amount, 1)  OVER (ORDER BY created_at) AS prev_amount,
    LEAD(amount, 1) OVER (ORDER BY created_at) AS next_amount
FROM orders;
```

#### 公用表表达式 (CTE, MySQL 8.0+)

```sql
-- 基本 CTE
WITH active_users AS (
    SELECT id, username, email FROM users WHERE status = 'active'
)
SELECT * FROM active_users WHERE age > 25;

-- 多 CTE
WITH
    user_stats AS (
        SELECT user_id, COUNT(*) AS order_count, SUM(amount) AS total
        FROM orders GROUP BY user_id
    ),
    high_value AS (
        SELECT * FROM user_stats WHERE total > 10000
    )
SELECT u.username, hv.order_count, hv.total
FROM users u
JOIN high_value hv ON u.id = hv.user_id;

-- 递归 CTE（生成序列 / 树形结构）
WITH RECURSIVE seq(n) AS (
    SELECT 1                           -- 初始
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 10 -- 递归
)
SELECT * FROM seq;

-- 递归 CTE：查询组织架构树
WITH RECURSIVE org_tree AS (
    SELECT id, name, manager_id, 1 AS level
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, t.level + 1
    FROM employees e
    JOIN org_tree t ON e.manager_id = t.id
)
SELECT * FROM org_tree ORDER BY level, name;
```

### 5.3 更新 (UPDATE)

```sql
-- 基本更新
UPDATE users SET status = 'active' WHERE id = 1;

-- 多字段更新
UPDATE users SET
    age = age + 1,
    updated_at = NOW()
WHERE status = 'active';

-- 从另一表更新
UPDATE users u
JOIN user_logs ul ON u.id = ul.user_id
SET u.last_login = ul.login_time
WHERE ul.action = 'login';

-- 用子查询更新
UPDATE products SET price = price * 1.1
WHERE category_id IN (
    SELECT id FROM categories WHERE name = '电子产品'
);

-- CASE WHEN 条件更新
UPDATE users SET status = CASE
    WHEN age < 18 THEN 'junior'
    WHEN age < 60 THEN 'active'
    ELSE 'senior'
END;

-- 更新并返回（MySQL 8.0+）
UPDATE users SET login_count = login_count + 1
WHERE id = 1 RETURNING id, username, login_count;
```

### 5.4 删除 (DELETE)

```sql
-- 条件删除
DELETE FROM users WHERE id = 1;

-- 批量条件删除
DELETE FROM users WHERE status = 'banned' AND updated_at < '2025-01-01';

-- 多表删除
DELETE u, o
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.status = 'deleted';

-- 只删除关联数据
DELETE o FROM orders o
INNER JOIN users u ON o.user_id = u.id
WHERE u.status = 'deleted';

-- 按排序删除前 N 条
DELETE FROM logs ORDER BY created_at ASC LIMIT 10000;

-- TRUNCATE：清空表（DDL，不可回滚，重置自增）
TRUNCATE TABLE temp_logs;

-- 区别：DELETE 逐行删除（可回滚），TRUNCATE 直接释放空间（DDL）
```

---

## 6. 索引

### 6.0 索引基础

**什么是索引？** 索引是存储引擎用于快速查找记录的一种**数据结构**，类似于书的目录。

**优点**：
- 大幅加快数据查找速度（B+树高度 2-4 层，最多 2-4 次磁盘 I/O）
- 加速排序和分组（索引天然有序）
- 加速表连接

**缺点**：
- 占用额外物理空间
- 写操作（INSERT/UPDATE/DELETE）需维护索引，影响性能

**何时建索引？** 经常用于 `WHERE` / `JOIN` / `ORDER BY` / `GROUP BY` 的字段。

**何时不建索引？** 表记录较少、频繁增删改、列参与运算、区分度低（如性别）的字段。

### 6.0a 索引数据结构

#### B+树索引（InnoDB 默认）

B+树在 B 树基础上，所有数据只存储在叶子节点，叶子节点之间通过顺序访问指针连接，形成有序链表。

```
                  [30 | 60]              ← 非叶子节点（仅存 key）
                 /    |    \
        [10|20]    [40|50]    [70|80]    ← 非叶子节点
        /  |  \    /  |  \    /  |  \
      [1]→[10]→[20]→[30]→[40]→[50]→[60]→[70]→...   ← 叶子节点（存数据 + 双向链表）
```

#### 为什么 B+树比 B 树更适合数据库索引？

- B+树数据都在叶子节点，**区间查询**只需遍历叶子链表，而 B 树需要中序遍历
- B+树非叶子节点只存 key，**单页可存更多 key**，树更矮，I/O 更少
- B+树查询路径长度固定（根→叶子），**查询效率稳定**

#### 哈希索引

基于哈希表实现，`key = hash(索引列) → value = 行指针`，查找 O(1)，**仅支持等值查询**。

| 对比 | B+树索引 | 哈希索引 |
|---|---|---|
| 范围查询 | ✅ | ❌ |
| 排序 | ✅ | ❌ |
| 模糊查询 | ✅ (最左前缀) | ❌ |
| 等值查询 | O(log n) | O(1) |
| 性能稳定性 | 稳定 | 哈希冲突时不稳定 |

> InnoDB 支持自适应哈希索引（Adaptive Hash Index），对热点数据自动建立哈希索引。

### 6.1 索引类型

```sql
-- ===== 普通索引 =====
CREATE INDEX idx_username ON users(username);
ALTER TABLE users ADD INDEX idx_username (username);

-- ===== 唯一索引 =====
CREATE UNIQUE INDEX uk_email ON users(email);
ALTER TABLE users ADD UNIQUE KEY uk_email (email);

-- ===== 主键索引（唯一 + 非空，每表仅一个）=====
ALTER TABLE users ADD PRIMARY KEY (id);

-- ===== 复合索引 =====
CREATE INDEX idx_status_age ON users(status, age);
-- 遵循最左前缀原则：WHERE status=... 可用，WHERE age=... 不可用

-- ===== 前缀索引（长字符串优化）=====
CREATE INDEX idx_email_prefix ON users(email(10));

-- ===== 全文索引 =====
CREATE FULLTEXT INDEX ft_content ON articles(title, content);
-- 使用：
SELECT * FROM articles WHERE MATCH(title, content) AGAINST('MySQL 优化' IN BOOLEAN MODE);

-- ===== 空间索引 =====
CREATE SPATIAL INDEX idx_location ON places(coordinates);

-- ===== 函数索引 (MySQL 8.0.13+) =====
CREATE INDEX idx_lower_email ON users((LOWER(email)));
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';
```

### 6.2 索引管理

```sql
-- 查看索引
SHOW INDEX FROM users;
SHOW KEYS FROM users;

-- 删除索引
DROP INDEX idx_username ON users;
ALTER TABLE users DROP INDEX idx_username;

-- 删除主键（需先去掉 AUTO_INCREMENT）
ALTER TABLE users MODIFY id BIGINT NOT NULL;
ALTER TABLE users DROP PRIMARY KEY;

-- 索引统计信息
ANALYZE TABLE users;

-- 查看索引使用情况
SELECT * FROM sys.schema_unused_indexes;

-- 冗余索引检查
SELECT * FROM sys.schema_redundant_indexes
WHERE table_schema = 'mydb';

-- 查看索引大小
SELECT
    table_name,
    index_name,
    stat_value * @@innodb_page_size AS size_bytes
FROM mysql.innodb_index_stats
WHERE database_name = 'mydb' AND table_name = 'users';
```

### 6.3 执行计划 (EXPLAIN)

```sql
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

EXPLAIN FORMAT=JSON
SELECT u.username, COUNT(o.id)
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
GROUP BY u.id;
```

**EXPLAIN 关键字段：**

| 字段 | 含义 | 理想值 |
|---|---|---|
| `type` | 访问类型 | `const` > `eq_ref` > `ref` > `range` > `index` > `ALL` |
| `key` | 使用的索引 | 非 NULL |
| `rows` | 扫描行数 | 越小越好 |
| `Extra` | 额外信息 | `Using index`（覆盖索引）最佳 |
| `key_len` | 索引使用长度 | 帮助判断是否用了完整索引 |

```sql
-- ⚠️ 避免 ALL（全表扫描）
-- 红灯信号：
-- type = ALL, rows 极大
-- Extra 含 "Using filesort"（文件排序）
-- Extra 含 "Using temporary"（临时表）
```

### 6.4 索引优化原则

```sql
-- ✅ 1. 遵循最左前缀原则（复合索引）
CREATE INDEX idx_a_b_c ON t(a, b, c);
-- ✅ WHERE a = ?                 可用
-- ✅ WHERE a = ? AND b = ?       可用
-- ✅ WHERE a = ? AND b = ? AND c 可用
-- ❌ WHERE b = ?                 不可用
-- ❌ WHERE c = ?                 不可用
-- ✅ WHERE a = ? AND c = ?       仅 a 生效（c 不生效）

-- ✅ 2. 避免在索引列上使用函数/运算
-- ❌ WHERE YEAR(created_at) = 2026;
-- ✅ WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01';

-- ✅ 3. 高选择性的列优先放入复合索引
-- 选择性 = DISTINCT 值数 / 总行数，越接近 1 越好

-- ✅ 4. 覆盖索引（查询列都在索引中）
CREATE INDEX idx_cover ON users(status, username, age);
SELECT username, age FROM users WHERE status = 'active';
-- Extra 显示 "Using index" 即覆盖索引

-- ❌ 5. 避免在 WHERE 中对索引列使用 OR（可能导致全表扫描）
-- ❌ SELECT * FROM users WHERE email = 'a' OR phone = 'b';
-- ✅ 使用 UNION：
SELECT * FROM users WHERE email = 'a'
UNION
SELECT * FROM users WHERE phone = 'b';

-- ❌ 6. LIKE 以 % 开头无法使用索引
-- ❌ WHERE username LIKE '%张三'
-- ✅ WHERE username LIKE '张三%'
```

### 6.5 聚集索引 vs 非聚集索引

**聚集索引（聚簇索引）**：叶子节点存储的是**整行数据**。InnoDB 的主键索引就是聚集索引。

**非聚集索引（二级索引）**：叶子节点存储的是**主键值**，需要**回表**才能获取完整行。

```
聚集索引（主键索引树）：                  二级索引（如 uk_email）：
     [主键范围]                              [email 范围]
    /    |    \                              /    |    \
  [叶子: 完整行]                             [叶子: email + 主键ID]
  包含 id,name,email,age...                 仅包含 email 和主键，需回表
```

**InnoDB 聚集索引选择规则**：
1. 有主键 → 使用主键
2. 无主键但有唯一非空索引 → 使用第一个唯一索引
3. 都没有 → InnoDB 自动生成 6 字节的隐藏 `ROW_ID`

### 6.6 覆盖索引

**查询的所有列都在索引中，不需要回表**，性能最优。

```sql
-- 联合索引: (user_id, blog_id)
CREATE INDEX idx_user_blog ON user_like(user_id, blog_id);

-- ✅ 覆盖索引：Extra = 'Using index'
EXPLAIN SELECT blog_id FROM user_like WHERE user_id = 13;
-- 查询列 blog_id 在索引中，WHERE 符合最左前缀 → 索引查找直达

-- ✅ 索引扫描覆盖：Extra = 'Using where; Using index'
EXPLAIN SELECT user_id FROM user_like WHERE blog_id = 1;
-- 查询列在索引中，但 WHERE 不符合最左前缀 → 索引扫描（不回表）
```

### 6.7 前缀索引

对长字符串列取前 N 个字符建索引，减少索引大小，提高查询速度。

```sql
-- 对 email 前 10 个字符建索引
ALTER TABLE users ADD INDEX idx_email_prefix (email(10));

-- 选择合适的前缀长度：确保选择性足够高
SELECT
    COUNT(DISTINCT LEFT(email, 5))  / COUNT(*) AS sel5,
    COUNT(DISTINCT LEFT(email, 10)) / COUNT(*) AS sel10,
    COUNT(DISTINCT LEFT(email, 15)) / COUNT(*) AS sel15
FROM users;
-- 选择性接近 1 且长度最短的那个即为最优
```

### 6.8 索引失效场景总结

| 场景 | 示例 | 原因 |
|---|---|---|
| 不满足最左前缀 | `WHERE c = 1`（索引是 a,b,c） | 跳过最左列 |
| LIKE 以 `%` 开头 | `WHERE name LIKE '%张'` | 无法定位起始位置 |
| 类型隐式转换 | `WHERE phone = 13800138000`（phone 是 VARCHAR） | 字符串不加引号 |
| 索引列运算 | `WHERE YEAR(created_at) = 2026` | 函数破坏了索引有序性 |
| 使用 `!=` / `NOT IN` | `WHERE status != 'banned'` | 优化器可能判定全表更快 |
| OR 连接 | `WHERE a = 1 OR b = 2`（不同列） | 可能全表扫描，改用 UNION |
| 范围查询后的列 | `WHERE a > 1 AND b = 2`（索引 a,b） | 范围列之后的索引失效 |

---

## 7. 事务与锁

### 7.1 事务 ACID 四大特性

**ACID**：**原子性**（Atomicity）、**一致性**（Consistency）、**隔离性**（Isolation）、**持久性**（Durability）。

- **原子性**：事务包含的所有操作要么全部成功，要么全部失败回滚。
- **一致性**：事务执行前后，数据库必须处于一致性状态。比如 A 与 B 账户共有 1000 元，两人之间转账后无论成功还是失败，账户总和仍是 1000。
- **隔离性**：多个并发事务相互隔离，一个事务的执行不应被其他事务干扰。具体的隔离程度由隔离级别决定。
- **持久性**：事务一旦提交，对数据的改变就是永久的，即使数据库系统遇到故障也不会丢失已提交的数据。

### 7.2 事务基础

```sql
-- 开启事务
START TRANSACTION;
-- 或
BEGIN;

-- 操作
INSERT INTO orders (user_id, amount) VALUES (1, 100);
UPDATE users SET balance = balance - 100 WHERE id = 1;

-- 提交
COMMIT;

-- 回滚
ROLLBACK;

-- 设置保存点
SAVEPOINT sp1;
-- ...操作...
ROLLBACK TO SAVEPOINT sp1;  -- 回滚到保存点
RELEASE SAVEPOINT sp1;      -- 释放保存点
```

### 7.3 事务隔离级别

先了解三个并发问题：**脏读**、**不可重复读**、**幻读**。

- **脏读**：事务 A 读取了事务 B **未提交**的数据，若 B 回滚，A 读到的就是"脏数据"。
- **不可重复读**：事务 A 内两次相同查询返回了不同结果，因为事务 B 在两次查询之间**修改**了数据并提交。
- **幻读**：事务 A 读取某个范围的数据时，事务 B 在该范围内**插入/删除**了新行，A 再次读取时发现行数变了。

**区别**：脏读是针对未提交数据；不可重复读是针对已提交的修改；幻读是针对已提交的插入/删除。

```sql
-- 查看当前隔离级别
SELECT @@transaction_isolation;  -- MySQL 8.0+
SELECT @@tx_isolation;           -- MySQL 5.x

-- 设置隔离级别（会话级）
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- 设置隔离级别（全局）
SET GLOBAL TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | InnoDB 默认 |
|---|---|---|---|---|
| `READ UNCOMMITTED` | ✗ | ✗ | ✗ | |
| `READ COMMITTED` | ✓ | ✗ | ✗ | |
| `REPEATABLE READ` | ✓ | ✓ | ✓ (MVCC 解决) | ✅ |
| `SERIALIZABLE` | ✓ | ✓ | ✓ | |

### 7.4 锁机制

```sql
-- ===== 表级锁 =====
LOCK TABLES users READ;   -- 读锁：其他可读不可写
LOCK TABLES users WRITE;  -- 写锁：其他不可读不可写
UNLOCK TABLES;

-- ===== 行级锁（InnoDB）=====
-- 排他锁（写锁）
SELECT * FROM users WHERE id = 1 FOR UPDATE;

-- 共享锁（读锁）
SELECT * FROM users WHERE id = 1 FOR SHARE;  -- MySQL 8.0+
SELECT * FROM users WHERE id = 1 LOCK IN SHARE MODE;  -- MySQL 5.x

-- 跳过已被锁定的行
SELECT * FROM users WHERE status = 'pending'
FOR UPDATE SKIP LOCKED;  -- MySQL 8.0+

-- 不等待，立即报错
SELECT * FROM users WHERE id = 1
FOR UPDATE NOWAIT;
```

### 7.5 共享锁 vs 排他锁

```sql
-- 共享锁（S 锁 / 读锁）：多个事务可同时持有，允许读，不允许写
SELECT * FROM users WHERE id = 1 FOR SHARE;

-- 排他锁（X 锁 / 写锁）：只允许一个事务持有，不允许其他事务读或写
SELECT * FROM users WHERE id = 1 FOR UPDATE;
```

| 对比 | 共享锁 (S) | 排他锁 (X) |
|---|---|---|
| **允许并发的 S 锁** | ✅ | ❌ |
| **允许并发的 X 锁** | ❌ | ❌ |
| **持有者可读** | ✅ | ✅ |
| **持有者可写** | ❌ | ✅ |

> `SELECT ... FOR UPDATE` 注意事项：仅适用于 InnoDB，必须在事务中生效。若 WHERE 条件不使用索引（或 `like`/`!=`），会升级为**表锁**。

### 7.6 乐观锁与悲观锁

**悲观锁**：假设并发冲突大概率发生，操作前先锁定数据。

```sql
-- MySQL 实现：SELECT ... FOR UPDATE
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;
-- 计算...
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;
```

**乐观锁**：假设并发冲突很少，提交时检查数据是否被修改。

```sql
-- 版本号机制（推荐）
-- 表结构需要 version 字段
UPDATE products
SET stock = stock - 1, version = version + 1
WHERE id = 1 AND version = 5;  -- 带上当前版本号
-- 若 affected_rows = 0，说明版本号已变，重试

-- CAS 思想：先查，更新时校验版本
SELECT id, stock, version FROM products WHERE id = 1;
-- version = 5
UPDATE products SET stock = stock - 1, version = version + 1
WHERE id = 1 AND version = 5;
```

---

## 8. MVCC 多版本并发控制

### 8.1 什么是 MVCC？

MVCC（Multiversion Concurrency Control）是同一条记录保留多个版本，实现读写不相互阻塞的并发控制机制。对于高并发场景，MVCC 比单纯加锁效率更高。

### 8.2 实现原理

MVCC 依赖**隐藏字段**和 **undo log 版本链**：

| 隐藏字段 | 说明 |
|---|---|
| `DB_TRX_ID` | 最近修改该行的事务 ID |
| `DB_ROLL_PTR` | 回滚指针，指向 undo log 中该行的上一个版本 |
| `DB_ROW_ID` | 隐藏主键（若表无主键则自动生成） |

**版本链形成过程**：

```
1. 初始数据：name='张三', age=10, DB_TRX_ID=0, DB_ROLL_PTR=NULL

2. 事务 A (trx_id=100) 将 age 改为 12：
   ┌──────────────────────────────────────────┐
   │ 当前行: name='张三', age=12              │
   │ DB_TRX_ID=100, DB_ROLL_PTR → undo log   │
   └──────────────────────────────────────────┘
                       ↓
   ┌──────────────────────────────────────────┐
   │ undo log: name='张三', age=10            │
   │ DB_TRX_ID=0, DB_ROLL_PTR=NULL           │
   └──────────────────────────────────────────┘

3. 事务 B (trx_id=200) 将 age 改为 8：
   ┌──────────────────────────────────────────┐
   │ 当前行: name='张三', age=8               │
   │ DB_TRX_ID=200, DB_ROLL_PTR → undo log   │
   └──────────────────────────────────────────┘
                       ↓
   ┌──────────────────────────────────────────┐
   │ undo log: name='张三', age=12            │
   │ DB_TRX_ID=100, DB_ROLL_PTR → ...        │
   └──────────────────────────────────────────┘
                       ↓
   ┌──────────────────────────────────────────┐
   │ undo log: name='张三', age=10            │
   │ DB_TRX_ID=0, DB_ROLL_PTR=NULL           │
   └──────────────────────────────────────────┘
```

### 8.3 Read View（读视图）

Read View 是事务在某一时刻的"数据快照"，包含：

- `up_limit_id`：当前活跃事务中最小的 trx_id
- `low_limit_id`：下一个即将分配的事务 trx_id
- 活跃事务链表：创建 Read View 时仍在活跃（未提交）的事务 ID 列表

**可见性判断规则**：

| 条件 | 结论 | 操作 |
|---|---|---|
| `DATA_TRX_ID < up_limit_id` | 修改该行的事务已提交 | ✅ 可见 |
| `DATA_TRX_ID >= low_limit_id` | 修改在 Read View 之后发生 | ❌ 不可见，沿版本链找上一个版本 |
| `up_limit_id <= DATA_TRX_ID < low_limit_id` | 判断是否在活跃链表中 | 在链表中 → ❌ 不可见；不在 → ✅ 可见 |

### 8.4 快照读与当前读

**快照读**：读取快照版本（通过 MVCC 实现，不加锁）

```sql
SELECT * FROM users WHERE id = 1;  -- 普通 SELECT 就是快照读
```

**当前读**：读取最新版本（加锁）

```sql
SELECT * FROM users WHERE id = 1 FOR UPDATE;   -- 当前读
SELECT * FROM users WHERE id = 1 LOCK IN SHARE MODE;  -- 当前读
UPDATE users SET name = 'x' WHERE id = 1;      -- 当前读
DELETE FROM users WHERE id = 1;                -- 当前读
INSERT INTO users VALUES (...);                -- 当前读
```

> **关键区别**：MVCC 只能在**快照读**下避免幻读。当前读场景下，MVCC 无法避免幻读，需要靠 **Next-Key Lock**（行锁 + 间隙锁）来解决。

**隔离级别与 Read View 创建时机**：

| 隔离级别 | Read View 创建时机 | 效果 |
|---|---|---|
| `READ COMMITTED` | **每次** SELECT 都创建新的 Read View | 能读到其他事务已提交的修改 |
| `REPEATABLE READ` | 事务内**第一次** SELECT 时创建，之后复用 | 事务内多次读取结果一致 |

---

## 9. MySQL 架构

### 9.1 整体架构

```
┌─────────────────────────────────────────────────┐
│                   Server 层                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  连接器   │→│ 查询缓存  │→│ 分析器（词法+语法）│ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│         ↓                        ↓              │
│  ┌──────────┐              ┌──────────┐         │
│  │  执行器   │←─────────────│  优化器   │         │
│  └────┬─────┘              └──────────┘         │
│       │ 调用引擎 API                              │
│  ┌────┴─────────────────────────────────────┐   │
│  │  binlog 模块（Server 层统一日志）           │   │
│  └──────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────┐
│                 存储引擎层                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  InnoDB  │ │  MyISAM  │ │  Memory/Archive  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Server 层组件：**

| 组件 | 作用 |
|---|---|
| **连接器** | 身份认证、权限校验、连接管理 |
| **查询缓存** | 命中则直接返回（MySQL 8.0 已移除） |
| **分析器** | 词法分析（提取关键字） + 语法分析（检查语法） |
| **优化器** | 选择索引、决定 JOIN 顺序、生成执行计划 |
| **执行器** | 权限校验后调用存储引擎接口，返回结果 |

### 9.2 三大日志：binlog / redo log / undo log

| 日志 | 层级 | 记录内容 | 作用 |
|---|---|---|---|
| **binlog** | Server 层 | 逻辑日志，记录 SQL 语句原始逻辑 | 主从复制、数据恢复 |
| **redo log** | InnoDB 引擎 | 物理日志，记录数据页的修改 | 崩溃恢复（crash-safe） |
| **undo log** | InnoDB 引擎 | 记录修改前的数据 | 事务回滚、MVCC 版本链 |

**binlog vs redo log 区别**：

| 对比 | binlog | redo log |
|---|---|---|
| 层级 | Server 层，所有引擎共用 | InnoDB 引擎专有 |
| 记录方式 | 逻辑日志（SQL 语句） | 物理日志（页修改） |
| 写入时机 | 事务提交前一次写入 | 事务过程中不断写入 |
| 用途 | 主从复制、数据恢复 | 崩溃恢复 |

```
innodb_flush_log_at_trx_commit 参数：
  0 — 每秒刷盘一次（性能最好，宕机可能丢 1 秒数据）
  1 — 每次提交刷盘（最安全，默认推荐）
  2 — 每次提交写 OS 缓存，每秒刷盘（折中）
```

### 9.3 查询语句执行流程

`SELECT * FROM user WHERE id > 1 AND name = '张三';`

1. **连接器**：校验身份和权限
2. **查询缓存**（MySQL 8.0 之前）：命中则直接返回
3. **分析器**：词法分析 → 提取表名、字段；语法分析 → 检查 SQL 是否正确
4. **优化器**：决定使用哪个索引（id 索引 vs name 索引），生成最优执行计划
5. **执行器**：校验权限 → 调用存储引擎接口 → 返回结果

### 9.4 更新语句执行流程（两阶段提交）

`UPDATE user SET name = '大彬' WHERE id = 1;`

```
执行器读取数据 ──→ 调用 InnoDB 接口
                         │
                         ▼
                  InnoDB 在内存中修改数据
                         │
                         ▼
                  写入 redo log（prepare 状态）
                         │
                         ▼
             执行器写入 binlog
                         │
                         ▼
             提交 redo log（commit 状态）
                         │
                         ▼
                    更新完成
```

> **为什么不先提交 redo log 再写 binlog？** 若写完 redo log 后宕机，binlog 未写入，机器重启后通过 redo log 恢复了数据，但 binlog 中没有该记录，导致主从复制时丢失该条数据。两阶段提交保证了 redo log 和 binlog 的逻辑一致性。

---

## 10. 视图、存储过程与触发器

### 10.1 视图

```sql
-- 创建视图
CREATE VIEW v_active_users AS
SELECT id, username, email, age, created_at
FROM users
WHERE status = 'active';

-- 使用视图
SELECT * FROM v_active_users WHERE age > 25;

-- 更新视图
CREATE OR REPLACE VIEW v_active_users AS
SELECT id, username, email, age, balance, created_at
FROM users WHERE status = 'active';

-- 查看所有视图
SHOW FULL TABLES WHERE table_type = 'VIEW';

-- 删除视图
DROP VIEW IF EXISTS v_active_users;
```

### 10.2 存储过程

```sql
-- 创建存储过程
DELIMITER $$

CREATE PROCEDURE sp_get_user_orders(IN p_user_id BIGINT, IN p_limit INT)
BEGIN
    SELECT o.id, o.order_no, o.amount, o.created_at
    FROM orders o
    WHERE o.user_id = p_user_id
    ORDER BY o.created_at DESC
    LIMIT p_limit;

    SELECT COUNT(*) AS total_orders
    FROM orders
    WHERE user_id = p_user_id;
END$$

DELIMITER ;

-- 调用
CALL sp_get_user_orders(1, 10);

-- 带输出参数
DELIMITER $$

CREATE PROCEDURE sp_get_user_count(IN p_status VARCHAR(20), OUT p_count INT)
BEGIN
    SELECT COUNT(*) INTO p_count FROM users WHERE status = p_status;
END$$

DELIMITER ;

CALL sp_get_user_count('active', @count);
SELECT @count;

-- 查看存储过程
SHOW PROCEDURE STATUS WHERE db = 'mydb';
SHOW CREATE PROCEDURE sp_get_user_orders;

-- 删除
DROP PROCEDURE IF EXISTS sp_get_user_orders;
```

### 10.3 函数

```sql
-- 创建函数
DELIMITER $$

CREATE FUNCTION fn_calc_age(birth_date DATE) RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    RETURN TIMESTAMPDIFF(YEAR, birth_date, CURDATE());
END$$

DELIMITER ;

-- 使用
SELECT username, fn_calc_age(birthday) AS age FROM users;
```

### 10.4 触发器

```sql
-- BEFORE INSERT 触发器：自动填充
DELIMITER $$

CREATE TRIGGER trg_users_before_insert
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
    IF NEW.username IS NULL OR NEW.username = '' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'username 不能为空';
    END IF;
    SET NEW.created_at = IFNULL(NEW.created_at, NOW());
    SET NEW.updated_at = NOW();
END$$

DELIMITER ;

-- AFTER INSERT 触发器：记录日志
DELIMITER $$

CREATE TRIGGER trg_users_after_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (table_name, record_id, action, created_at)
    VALUES ('users', NEW.id, 'INSERT', NOW());
END$$

DELIMITER ;

-- 查看与删除
SHOW TRIGGERS;
DROP TRIGGER IF EXISTS trg_users_before_insert;
```

### 10.5 事件（定时任务）

```sql
-- 开启事件调度器
SET GLOBAL event_scheduler = ON;

-- 创建定时清理事件
CREATE EVENT evt_clean_expired_logs
ON SCHEDULE EVERY 1 DAY
STARTS '2026-07-04 03:00:00'
DO
    DELETE FROM logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- 查看事件
SHOW EVENTS;

-- 删除事件
DROP EVENT IF EXISTS evt_clean_expired_logs;
```

---

## 11. 存储引擎详解

### 11.1 引擎概览对比

| 特性 | **InnoDB** | **MyISAM** | **Memory** | **Archive** | **NDB** |
|---|---|---|---|---|---|
| **事务支持** | ✅ ACID | ❌ | ❌ | ❌ | ✅ |
| **行级锁** | ✅ | ❌ 表锁 | ❌ 表锁 | ❌ 行锁 | ✅ |
| **外键** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **MVCC** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **崩溃恢复** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **全文索引** | ✅ (5.6+) | ✅ | ❌ | ❌ | ❌ |
| **GIS/空间索引** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **压缩** | ✅ | ✅ myisampack | ❌ | ✅ 自动压缩 | ❌ |
| **缓存数据** | ✅ | ✅ 仅索引 | ✅ | ❌ | ✅ |
| **集群** | 复制集 | 复制集 | ❌ | ❌ | ✅ 原生分布式 |
| **存储限制** | 64TB | 256TB | RAM | 无 | 384EB |
| **默认引擎** | ✅ 5.5+ | 5.5 之前 | ❌ | ❌ | ❌ |

### 11.2 InnoDB（推荐）

**MySQL 5.5+ 默认引擎，满足绝大多数场景。**

```
结构特点：
┌────────────────────────────────────┐
│          InnoDB 引擎架构            │
│                                    │
│  ┌──────────────────────────────┐  │
│  │     缓冲池 (Buffer Pool)      │  │
│  │   • 缓存数据和索引页           │  │
│  │   • 建议占物理内存的 70-80%   │  │
│  └──────────────────────────────┘  │
│                                    │
│  ┌──────────────┐ ┌────────────┐  │
│  │ redo log     │ │ undo log   │  │
│  │ (重做日志)    │ │ (回滚日志)  │  │
│  │ WAL 机制     │ │ MVCC 基础  │  │
│  └──────────────┘ └────────────┘  │
│                                    │
│  ┌──────────────────────────────┐  │
│  │  Doublewrite Buffer (双写缓冲) │  │
│  │  防止页断裂 (partial write)   │  │
│  └──────────────────────────────┘  │
│                                    │
│  ┌──────────────────────────────┐  │
│  │  Adaptive Hash Index (自适应) │  │
│  │  Change Buffer (插入缓冲)     │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
```

**核心特性：**

```sql
-- 1. 事务与 MVCC（多版本并发控制）
-- 读不阻塞写，写不阻塞读，基于 undo log 实现

-- 2. 行级锁 + 间隙锁 (Next-Key Lock)
-- 防止幻读，REPEATABLE READ 下默认

-- 3. 插入缓冲 (Change Buffer)
-- 对非唯一二级索引的插入/更新进行合并写，减少随机 I/O

-- 4. 两次写 (Doublewrite)
-- 16KB 页写入时，先写到 doublewrite buffer，再刷到数据文件
-- 防止页断裂导致数据损坏

-- 5. 自适应哈希索引 (Adaptive Hash Index)
-- 对热点数据自动建立哈希索引，加速等值查询

-- 6. 热备份
-- 支持 mysqlbackup、XtraBackup 在线热备
```

**InnoDB 核心参数：**

```ini
[mysqld]
# 缓冲池大小（最重要的参数，建议物理内存的 70-80%）
innodb_buffer_pool_size = 8G

# 日志文件大小（越大恢复越慢，但写入性能越好）
innodb_log_file_size = 1G
innodb_log_files_in_group = 2

# 刷盘策略（1: 每次提交刷盘，最安全）
innodb_flush_log_at_trx_commit = 1

# 刷新方式（O_DIRECT 跳过 OS 缓存，避免双重缓存）
innodb_flush_method = O_DIRECT

# 独立表空间（每个表一个 .ibd 文件，推荐）
innodb_file_per_table = ON

# 读写 I/O 线程数
innodb_read_io_threads = 4
innodb_write_io_threads = 4

# 并发线程数
innodb_thread_concurrency = 0  # 0 = 不限制
```

### 11.3 MyISAM

**MySQL 5.5 之前的默认引擎，不支持事务。**

```sql
-- 适用场景（很少）：
-- 1. 只读或读远大于写的场景（数据仓库、日志分析）
-- 2. 不需要事务的场景
-- 3. 对并发要求不高的场景

-- 缺点：
-- ❌ 无事务    ❌ 无行级锁（仅表锁）
-- ❌ 无外键    ❌ 崩溃恢复差（需要修复表）
-- ❌ 仅缓存索引，不缓存数据（依赖 OS 缓存）
```

| 对比项 | InnoDB | MyISAM |
|---|---|---|
| **存储文件** | `.ibd` (数据+索引) | `.MYD` 数据 + `.MYI` 索引 |
| **计数速度** | `COUNT(*)` 全表扫描 | `COUNT(*)` 直接读取（无 WHERE 时） |
| **全文索引** | 5.6+ 支持 | 原生支持 |
| **并发写入** | 行锁，并发高 | 表锁，串行写入 |
| **压缩只读表** | 不支持 | myisampack 支持 |
| **MERGE 表** | 分区表替代 | 支持 MERGE 存储引擎 |

### 11.4 Memory（HEAP）

```sql
-- 数据全部存在内存中，重启后数据丢失，结构保留
CREATE TABLE tmp_cache (
    id   INT,
    data VARCHAR(100)
) ENGINE = Memory;

-- 适用场景：
-- ✅ 临时表、会话缓存、中间计算结果
-- ✅ 需要极快访问速度的非持久化数据

-- 注意：
-- ❌ 表级锁，并发受限
-- ❌ VARCHAR = CHAR（定长存储），浪费内存
-- ❌ 不支持 TEXT/BLOB
-- ❌ max_heap_table_size 限制表大小
```

### 11.5 Archive

```sql
-- 高压缩比（约 1:10 ~ 1:15），只支持 INSERT 和 SELECT
CREATE TABLE archived_logs (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    message    VARCHAR(1000),
    created_at DATETIME
) ENGINE = Archive;

-- 适用场景：
-- ✅ 日志归档、审计记录
-- ✅ 写入后不修改的数据
-- ✅ 需要压缩节省空间

-- 限制：
-- ❌ 不支持 UPDATE、DELETE
-- ❌ 不支持索引（主键除外，5.0+）
-- ❌ 读操作慢（需解压）
```

### 11.6 CSV

```sql
-- 数据以 CSV 格式直接存储为文本文件，可在数据库外部查看/编辑
CREATE TABLE csv_data (
    id   INT NOT NULL,
    name VARCHAR(50) NOT NULL
) ENGINE = CSV;

-- 适用场景：
-- ✅ 与其他系统交换数据
-- ✅ 快速导出/导入 CSV

-- 限制：
-- ❌ 不支持索引
-- ❌ 不支持 NULL（NOT NULL）
-- ❌ 不支持分区
```

### 11.7 NDB（MySQL Cluster）

```sql
-- 原生分布式集群引擎，数据自动分片
-- 适用场景：
-- ✅ 需要 99.999% 高可用的电信级应用
-- ✅ 高吞吐、低延迟的分布式 OLTP

-- 限制：
-- ❌ JOIN 性能差（在数据节点执行）
-- ❌ 复杂查询弱于 InnoDB
-- ❌ 操作复杂度高
-- ❌ 将所有数据加载到内存
```

### 11.8 引擎选择决策树

```
需要事务支持？
    ├── YES → InnoDB（99% 情况）
    │
    └── NO →
        │
        需要全文索引？
        │   ├── MySQL 5.5 → MyISAM
        │   └── MySQL 5.6+ → InnoDB 就够了
        │
        纯读场景，不需要事务？
        │   └── 仍然推荐 InnoDB（崩溃恢复更强）
        │
        临时缓存数据？
            └── Memory（重启会丢，适合短期）
```

> **结论：几乎所有场景都选 InnoDB。** MyISAM 仅极少数遗留系统还在使用，新项目一律用 InnoDB。

---

## 12. 主从复制

### 12.1 复制原理

```
┌──────────────┐   binlog    ┌──────────────┐
│   Master     │────────────►│   Slave      │
│   (主库)      │             │   I/O 线程    │
│   binlog dump│             │   ↓ relay log│
└──────────────┘             │   SQL 线程    │
                             │   ↓ 执行变更  │
                             │   从库数据    │
                             └──────────────┘

三种格式：
• STATEMENT  — 记录 SQL 语句（可能不一致）
• ROW        — 记录行变更（推荐，最安全）
• MIXED      — 混合模式
```

### 12.2 主库配置

```ini
# my.cnf — Master
[mysqld]
server-id = 1                      # 唯一 ID
log-bin = mysql-bin                # 开启 binlog
binlog_format = ROW                # 行格式（推荐）
binlog_row_image = FULL           # 记录完整行
sync_binlog = 1                   # 每次提交刷盘
expire_logs_days = 7              # binlog 保留天数
max_binlog_size = 500M            # 单个 binlog 文件大小
```

```sql
-- 创建复制用户
CREATE USER 'repl'@'%' IDENTIFIED BY 'repl_password';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
FLUSH PRIVILEGES;

-- 查看 binary log 位点
SHOW MASTER STATUS;
-- +------------------+----------+
-- | File             | Position |
-- +------------------+----------+
-- | mysql-bin.000001 |      1234|
-- +------------------+----------+
```

### 12.3 从库配置

```ini
# my.cnf — Slave
[mysqld]
server-id = 2
relay_log = relay-bin
read_only = ON                     # 从库只读
log-bin = mysql-bin                # 如果需要级联复制
```

```sql
-- 设置主库连接信息
CHANGE MASTER TO
    MASTER_HOST = '192.168.1.100',
    MASTER_PORT = 3306,
    MASTER_USER = 'repl',
    MASTER_PASSWORD = 'repl_password',
    MASTER_LOG_FILE = 'mysql-bin.000001',
    MASTER_LOG_POS  = 1234;          -- 从上一步 SHOW MASTER STATUS 获取

-- 启动复制
START SLAVE;  -- MySQL 5.x
START REPLICA; -- MySQL 8.0+

-- 查看复制状态
SHOW SLAVE STATUS\G  -- MySQL 5.x
SHOW REPLICA STATUS\G -- MySQL 8.0+
-- 关键字段：Slave_IO_Running, Slave_SQL_Running, Seconds_Behind_Master

-- 停止复制
STOP SLAVE;
STOP REPLICA;

-- 重置复制
RESET SLAVE ALL;
```

### 12.4 GTID 复制 (MySQL 5.6+，推荐)

```ini
# 主库和从库都配置
[mysqld]
gtid_mode = ON
enforce_gtid_consistency = ON
```

```sql
-- 从库使用 GTID 自动定位
CHANGE MASTER TO
    MASTER_HOST = '192.168.1.100',
    MASTER_PORT = 3306,
    MASTER_USER = 'repl',
    MASTER_PASSWORD = 'repl_password',
    MASTER_AUTO_POSITION = 1;  -- 自动定位，无需手动指定 log file & pos

-- 跳过 GTID 事务（错误处理）
SET GTID_NEXT = 'aaa-bbb-ccc:123';
BEGIN; COMMIT;
SET GTID_NEXT = 'AUTOMATIC';
```

---

## 13. 分库分表与大表优化

### 13.1 什么时候需要分库分表？

当单表数据量达到 **1000W** 或 **100G** 以后，索引优化、加从库等手段效果不明显时，需要考虑切分。

### 13.2 垂直拆分

按**业务模块**拆分数据库或表。

```
购物系统：
  商品库（商品基本信息、商品描述）
  订单库（订单主表、订单明细）
  用户库（用户信息、收货地址）
```

**优点**：行记录变小，数据页可存更多记录，减少 I/O。  
**缺点**：主键冗余，JOIN 操作跨库（可在业务层做 JOIN）；单表数据量仍可能过大。

### 13.3 水平拆分

按一定规则（如 ID 范围、哈希、时间）将数据分散到多个库/表中，每个库/表结构一致。

```sql
-- 按用户 ID 取模拆分
-- user_0: user_id % 4 = 0
-- user_1: user_id % 4 = 1
-- user_2: user_id % 4 = 2
-- user_3: user_id % 4 = 3

-- 按年份拆分
-- orders_2024, orders_2025, orders_2026
```

**优点**：单库/表数据量减少，性能提升；拆分后表结构相同，程序改动少。  
**缺点**：分片事务一致性难解决；跨节点 JOIN 性能差；扩容时需要数据迁移。

### 13.4 大表优化总结

| 方案 | 措施 |
|---|---|
| **限定数据范围** | 查询时限制时间范围（如仅查近一个月） |
| **读写分离** | 主库写、从库读，支撑更大并发 |
| **缓存** | 用 Redis 缓存热点数据 |
| **垂直拆分** | 按业务维度分库，核心字段和扩展字段分表 |
| **水平拆分** | 按 ID/哈希/时间分库分表 |

---

## 14. 分区表

### 14.1 什么是分区表？

分区表是一个独立的逻辑表，底层由多个物理子表组成。查询时引擎只访问相关分区，减少扫描量。

### 14.2 RANGE 分区（范围分区）

```sql
CREATE TABLE order_partition (
    id         INT AUTO_INCREMENT,
    order_date DATETIME,
    amount     DECIMAL(10,2),
    PRIMARY KEY (id, order_date)
)
PARTITION BY RANGE (TO_DAYS(order_date)) (
    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
    PARTITION p202403 VALUES LESS THAN (TO_DAYS('2024-04-01')),
    PARTITION p202404 VALUES LESS THAN (TO_DAYS('2024-05-01'))
);
```

### 14.3 LIST 分区（列表分区）

```sql
CREATE TABLE user_region (
    id       INT AUTO_INCREMENT,
    region   TINYINT,
    username VARCHAR(50),
    PRIMARY KEY (id, region)
)
PARTITION BY LIST(region) (
    PARTITION p_north VALUES IN (1, 2, 3),
    PARTITION p_south VALUES IN (4, 5, 6),
    PARTITION p_east  VALUES IN (7, 8, 9)
);
```

### 14.4 HASH 分区（哈希分区）

```sql
CREATE TABLE user_hash (
    id        INT AUTO_INCREMENT,
    user_name VARCHAR(50),
    PRIMARY KEY (id)
)
PARTITION BY HASH(id) PARTITIONS 4;
```

### 14.5 分区表的注意事项

- 打开和锁住所有底层表有成本 —— 分区过滤之前就已发生
- 重组分区需先创建临时分区，复制数据，再删除原分区，成本高
- 所有分区必须使用相同的存储引擎
- `WHERE` 条件匹配分区键时可以**分区裁剪**，只访问相关分区

---

## 15. 常用命令速查

### 系统信息

```sql
-- 版本
SELECT VERSION();

-- 当前用户
SELECT USER(), CURRENT_USER();

-- 数据库大小
SELECT table_schema AS '数据库',
       ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS '大小(MB)'
FROM information_schema.tables
GROUP BY table_schema;

-- 所有变量
SHOW VARIABLES;
SHOW VARIABLES LIKE '%buffer_pool%';
SHOW VARIABLES LIKE '%timeout%';

-- 状态
SHOW STATUS;
SHOW STATUS LIKE '%threads%';
SHOW STATUS LIKE 'Com_%';  -- 各类操作计数

-- 进程列表
SHOW PROCESSLIST;
SHOW FULL PROCESSLIST;
```

### 用户与权限

```sql
-- 创建用户
CREATE USER 'app'@'%' IDENTIFIED BY 'strong_password';
CREATE USER 'app'@'localhost' IDENTIFIED BY 'strong_password';

-- 授权
GRANT SELECT, INSERT, UPDATE, DELETE ON mydb.* TO 'app'@'%';
GRANT ALL PRIVILEGES ON mydb.* TO 'admin'@'%';
GRANT SELECT ON *.* TO 'readonly'@'%';  -- 只读全局

-- 查看权限
SHOW GRANTS FOR 'app'@'%';

-- 回收权限
REVOKE DELETE ON mydb.* FROM 'app'@'%';

-- 修改密码
ALTER USER 'app'@'%' IDENTIFIED BY 'new_password';

-- 删除用户
DROP USER 'app'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 备份与恢复

```bash
# ===== mysqldump =====
# 备份单个数据库
mysqldump -u root -p mydb > mydb_backup.sql

# 只备份结构
mysqldump -u root -p --no-data mydb > mydb_schema.sql

# 备份多个数据库
mysqldump -u root -p --databases db1 db2 > multi_db.sql

# 备份所有数据库
mysqldump -u root -p --all-databases > all_db.sql

# 备份单个表
mysqldump -u root -p mydb users orders > tables.sql

# 带锁备份（InnoDB 可在线）
mysqldump -u root -p --single-transaction --routines --triggers mydb > mydb.sql

# 恢复
mysql -u root -p mydb < mydb_backup.sql
mysql -u root -p < all_db.sql  # 压缩恢复

# ===== 二进制日志时间点恢复 =====
# 恢复从 binlog 指定位置
mysqlbinlog mysql-bin.000001 --start-position=1234 --stop-position=5678 | mysql -u root -p

# 按时间恢复
mysqlbinlog mysql-bin.000001 --start-datetime="2026-07-03 10:00:00" \
    --stop-datetime="2026-07-03 12:00:00" | mysql -u root -p
```

### 性能优化速查

```sql
-- 慢查询
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 2;  -- 超过 2 秒记录

-- 查看慢查询日志
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- 连接数
SHOW VARIABLES LIKE 'max_connections';
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- 表锁争用
SHOW STATUS LIKE 'Table_locks%';

-- InnoDB 缓冲池命中率
SELECT
    (1 - (SUM(innodb_buffer_pool_reads) / SUM(innodb_buffer_pool_read_requests))) * 100
    AS buffer_pool_hit_rate
FROM information_schema.global_status
WHERE variable_name IN ('innodb_buffer_pool_reads', 'innodb_buffer_pool_read_requests');
-- 理想值 > 99%
```

---

## 附：SQL 常用函数速查

### 字符串函数

| 函数 | 示例 | 结果 |
|---|---|---|
| `CONCAT()` | `CONCAT('Hello',' ','World')` | `Hello World` |
| `SUBSTRING()` | `SUBSTRING('MySQL', 1, 2)` | `My` |
| `LENGTH()` | `LENGTH('你好')` | `6` (字节) |
| `CHAR_LENGTH()` | `CHAR_LENGTH('你好')` | `2` (字符) |
| `LOWER()` / `UPPER()` | `UPPER('abc')` | `ABC` |
| `TRIM()` | `TRIM(' abc ')` | `abc` |
| `REPLACE()` | `REPLACE('abc','b','x')` | `axc` |
| `INSTR()` | `INSTR('MySQL','SQL')` | `3` |
| `LPAD()` | `LPAD('5', 3, '0')` | `005` |

### 日期函数

| 函数 | 说明 |
|---|---|
| `NOW()` | 当前日期时间 `2026-07-03 10:30:00` |
| `CURDATE()` | 当前日期 |
| `DATE_FORMAT(d, '%Y-%m-%d')` | 格式化 |
| `DATEDIFF(d1, d2)` | 日期差（天数）|
| `TIMESTAMPDIFF(MONTH, d1, d2)` | 日期差（月）|
| `DATE_ADD(d, INTERVAL 7 DAY)` | 加 7 天 |
| `DATE_SUB(d, INTERVAL 1 MONTH)` | 减 1 月 |
| `EXTRACT(YEAR FROM d)` | 提取年份 |
| `DAYOFWEEK(d)` | 星期几（1=周日）|
| `LAST_DAY(d)` | 当月最后一天 |

### 数值函数

| 函数 | 说明 |
|---|---|
| `ROUND(3.1415, 2)` → `3.14` | 四舍五入 |
| `CEIL(3.1)` → `4` | 向上取整 |
| `FLOOR(3.9)` → `3` | 向下取整 |
| `ABS(-10)` → `10` | 绝对值 |
| `MOD(10, 3)` → `1` | 取模 |
| `RAND()` | 随机数 [0,1) |
| `TRUNCATE(3.141, 2)` → `3.14` | 截断 |

### 条件函数

| 函数 | 说明 |
|---|---|
| `IF(条件, 真值, 假值)` | 三元运算 |
| `IFNULL(val, default)` | NULL 时返回默认 |
| `COALESCE(v1, v2, v3)` | 返回第一个非 NULL |
| `NULLIF(a, b)` | a=b 返回 NULL，否则返回 a |
| `CASE WHEN ... THEN ... ELSE ... END` | 多条件分支 |

---

## 附二：高频面试 FAQ

### Q1: `EXISTS` 和 `IN` 的区别？

```sql
-- EXISTS：外层表驱动，遍历外表每行代入子查询判断
SELECT * FROM A WHERE EXISTS (SELECT 1 FROM B WHERE B.id = A.id);

-- IN：子查询先执行，结果放临时表，再遍历临时表匹配外表
SELECT * FROM A WHERE id IN (SELECT id FROM B);
```

| 场景 | 推荐 |
|---|---|
| 子查询表（内表）较大 | `EXISTS`（减少总循环次数） |
| 外查询表（外表）较大 | `IN`（减少外表的遍历次数） |

### Q2: `TRUNCATE` / `DELETE` / `DROP` 的区别？

| | DELETE | TRUNCATE | DROP |
|---|---|---|---|
| 删除内容 | 数据行（可带 WHERE） | 全部数据 | 整个表（结构+数据+索引） |
| 语句类型 | DML | DDL | DDL |
| 是否可回滚 | ✅ | ❌ | ❌ |
| 触发器 | ✅ 触发 | ❌ 不触发 | ❌ |
| 自增值 | 保留 | 重置 | — |
| 速度 | 慢（逐行删除） | 快（直接释放） | 最快 |

### Q3: `WHERE` 和 `HAVING` 的区别？

- `WHERE`：分组**前**过滤行，作用于表和视图
- `HAVING`：分组**后**过滤组，作用于聚合结果

```sql
-- WHERE 不能使用聚合函数
-- ❌ SELECT dept, COUNT(*) FROM emp WHERE COUNT(*) > 5 GROUP BY dept;
-- ✅ SELECT dept, COUNT(*) FROM emp GROUP BY dept HAVING COUNT(*) > 5;
```

### Q4: `INT(10)` 和 `CHAR(10)` 的区别？

- `INT(10)`：`10` 是**显示宽度**（需配合 `ZEROFILL`），不影响存储范围
- `CHAR(10)`：`10` 是**存储长度**，始终占用 10 个字符空间（不足补空格）

### Q5: 主从同步有什么作用？

1. **读写分离**：主库写、从库读，支撑更大并发
2. **数据备份**：从库作为实时备份
3. **分析查询**：在从库执行复杂分析，不影响主库性能

### Q6: `SHOW PROCESSLIST` 的用途？

查看当前连接和正在执行的 SQL，快速定位慢查询和锁等待。

```sql
SHOW FULL PROCESSLIST;

-- 关键字段：
-- id: 线程 ID（可用 KILL id 终止）
-- Time: 执行时间（秒）
-- State: Sending data / Locked / Sorting for order 等
-- Info: 正在执行的 SQL
```

### Q7: `INT` 和 `BIGINT` 如何选择？

| 类型 | 范围 | 主键建议 |
|---|---|---|
| `INT` | -21 亿 ~ 21 亿 | 中小型表 |
| `BIGINT` | 极大范围 | 推荐（避免主键溢出） |
| `INT UNSIGNED` | 0 ~ 42 亿 | 确定无负值时可用 |

> 现代应用建议主键统一使用 `BIGINT UNSIGNED`，避免后期主键耗尽需要迁移。
