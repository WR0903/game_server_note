## 目录

1. [概述与安装](#1-概述与安装)

2. [连接 MongoDB](#2-连接-mongodb)

3. [数据库操作](#3-数据库操作)

4. [集合操作](#4-集合操作)

5. [文档 CRUD](#5-文档-crud)

   - [插入文档](#51-插入文档)

   - [查询文档](#52-查询文档)

   - [更新文档](#53-更新文档)

   - [删除文档](#54-删除文档)

6. [索引](#6-索引)

7. [聚合管道](#7-聚合管道)

8. [复制集（Replica Set）](#8-复制集replica-set)

9. [分片集群（Sharding）](#9-分片集群sharding)

10. [常用命令速查](#10-常用命令速查)

---

## 1. 概述与安装

### MongoDB 核心概念

| SQL 术语 | MongoDB 术语 | 说明 |
| --- | --- | --- |
| Database | Database | 数据库 |
| Table | Collection | 集合（表） |
| Row | Document | 文档（行） |
| Column | Field | 字段（列） |
| Primary Key | `_id` | 主键，ObjectId 自动生成 |
| Join | `$lookup` | 关联查询 |

### 文档结构（BSON）

```json
{
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "name": "张三",
    "age": 28,
    "email": "zhangsan@example.com",
    "address": {
        "city": "北京",
        "street": "长安街 100 号"
    },
    "hobbies": ["读书", "游泳", "编程"],
    "createdAt": ISODate("2026-01-15T08:00:00Z")
}
```

---

## 2. 连接 MongoDB

### 2.1 Shell 连接（mongosh）

```bash
# 连接本地默认端口
mongosh
# 连接指定主机和端口
mongosh --host 192.168.1.100 --port 27017
# 带认证连接
mongosh -u admin -p password --authenticationDatabase admin
# 连接字符串
mongosh "mongodb://user:pass@host1:27017,host2:27017/dbname?replicaSet=rs0"
# 连接 Atlas（云数据库）
mongosh "mongodb+srv://cluster0.xxxxx.mongodb.net/mydb" -u user -p pass
```

### 2.2 驱动程序连接示例

#### Node.js (mongoose)

```javascript
const mongoose = require('mongoose');
// 单节点连接
await mongoose.connect('mongodb://localhost:27017/mydb');
// 复制集连接
await mongoose.connect('mongodb://host1:27017,host2:27017,host3:27017/mydb?replicaSet=rs0', {
    maxPoolSize: 10,
    minPoolSize: 2,
    serverSelectionTimeoutMS: 5000,
    socketTimeoutMS: 45000,
});
// 分片集群连接（通过 mongos）
await mongoose.connect('mongodb://mongos1:27017,mongos2:27017/mydb');
```

#### Python (pymongo)

```python
from pymongo import MongoClient
# 基本连接
client = MongoClient('mongodb://localhost:27017/')
# 带连接池的连接
client = MongoClient(
    host=['host1:27017', 'host2:27017', 'host3:27017'],
    replicaSet='rs0',
    maxPoolSize=50,
    minPoolSize=5,
    connectTimeoutMS=3000,
    serverSelectionTimeoutMS=5000
)
db = client['mydb']
collection = db['users']
```

#### Go (mongo-driver)

```go
import (
    "context"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"
)
ctx := context.Background()
clientOpts := options.Client().
    ApplyURI("mongodb://localhost:27017").
    SetMaxPoolSize(20)
client, err := mongo.Connect(ctx, clientOpts)
defer client.Disconnect(ctx)
db := client.Database("mydb")
coll := db.Collection("users")
```

---

## 3. 数据库操作

```javascript
// 查看所有数据库
show dbs
// 切换/创建数据库（创建需写入数据后才生效）
use mydb
// 查看当前数据库
db
// 查看当前数据库统计信息
db.stats()
// 删除数据库
db.dropDatabase()
// 查看当前数据库所有集合
show collections
```

---

## 4. 集合操作

```javascript
// 显式创建集合（带选项）
db.createCollection("users", {
    capped: false,          // 上限集合（固定大小）
    // size: 10485760,      // capped 集合最大字节数
    // max: 5000,           // capped 集合最大文档数
    validator: {            // 文档校验规则
        $jsonSchema: {
            bsonType: "object",
            required: ["name", "email"],
            properties: {
                name: { bsonType: "string", description: "必填，姓名" },
                email: { bsonType: "string", pattern: "^.+@.+$" },
                age: { bsonType: "int", minimum: 0, maximum: 150 }
            }
        }
    },
    validationLevel: "strict",   // strict | moderate
    validationAction: "error"    // error | warn
})
// 删除集合
db.users.drop()
// 重命名集合
db.users.renameCollection("customers")
// 查看集合信息
db.users.stats()
```

---

## 5. 文档 CRUD

### 5.1 插入文档

```javascript
// 插入单条文档
db.users.insertOne({
    name: "张三",
    age: 28,
    email: "zhangsan@example.com",
    tags: ["开发", "架构"],
    status: "active",
    createdAt: new Date()
})
// 返回: { acknowledged: true, insertedId: ObjectId("...") }
// 插入多条文档
db.users.insertMany([
    { name: "李四", age: 32, email: "lisi@example.com", tags: ["测试"] },
    { name: "王五", age: 25, email: "wangwu@example.com", tags: ["前端", "设计"] },
    { name: "赵六", age: 35, email: "zhaoliu@example.com", tags: ["后端", "架构"] }
])
// 带选项的批量插入
db.users.insertMany(
    [
        { name: "A", age: 20 },
        { name: "B", age: 25 }
    ],
    { ordered: false }  // false: 遇到错误继续插入剩余文档
)
// insert() 通用方法（兼容旧版）
db.users.insert({ name: "旧版插入" })
```

### 5.2 查询文档

#### 基本查询

```javascript
// 查询所有文档
db.users.find()
// 格式化输出
db.users.find().pretty()
// 查询第一条
db.users.findOne({ name: "张三" })
// 条件查询
db.users.find({ age: 28 })
db.users.find({ age: { $gt: 25 } })          // 大于
db.users.find({ age: { $gte: 25 } })         // 大于等于
db.users.find({ age: { $lt: 30 } })          // 小于
db.users.find({ age: { $lte: 30 } })         // 小于等于
db.users.find({ age: { $ne: 28 } })          // 不等于
db.users.find({ age: { $in: [25, 28, 30] } })   // 在列表中
db.users.find({ age: { $nin: [25, 30] } })       // 不在列表中
```

#### 逻辑组合

```javascript
// AND 条件（多个字段，逗号分隔）
db.users.find({ age: { $gte: 25 }, status: "active" })
// OR 条件
db.users.find({
    $or: [
        { age: { $lt: 25 } },
        { status: "inactive" }
    ]
})
// NOR 条件
db.users.find({
    $nor: [
        { age: { $lt: 25 } },
        { status: "inactive" }
    ]
})
// NOT 条件
db.users.find({
    age: { $not: { $gte: 25 } }
})
// AND + OR 组合
db.users.find({
    status: "active",
    $or: [
        { age: { $lt: 25 } },
        { tags: "架构" }
    ]
})
```

#### 数组查询

```javascript
// 数组包含某元素
db.users.find({ tags: "架构" })
// 数组同时包含多个元素（不考虑顺序）
db.users.find({ tags: { $all: ["开发", "架构"] } })
// 数组元素个数匹配
db.users.find({ tags: { $size: 2 } })
// $elemMatch：数组中至少一个元素满足所有条件
db.orders.find({
    items: {
        $elemMatch: { product: "手机", quantity: { $gte: 2 } }
    }
})
// 按数组索引匹配
db.users.find({ "tags.0": "开发" })  // 第一个元素为 "开发"
```

#### 嵌套文档查询

```javascript
// 精确匹配嵌套文档（字段顺序必须一致）
db.users.find({ address: { city: "北京", street: "长安街 100 号" } })
// 点表示法（推荐，不受字段顺序影响）
db.users.find({ "address.city": "北京" })
db.users.find({ "address.city": "北京", "address.street": /^长安/ })
```

#### 投影（选择返回字段）

```javascript
// 只返回特定字段
db.users.find({}, { name: 1, email: 1, _id: 0 })
// 排除字段
db.users.find({ status: "active" }, { password: 0 })
// 数组投影 — $slice 返回数组前 N 个元素
db.users.find({}, { tags: { $slice: 2 } })
```

#### 游标操作

```javascript
// 排序（1: 升序, -1: 降序）
db.users.find().sort({ age: -1 })
db.users.find().sort({ age: 1, name: 1 })  // 多字段排序
// 跳过和限制（分页）
db.users.find().skip(10).limit(5)  // 跳过前 10 条，取 5 条
// 计数
db.users.countDocuments({ status: "active" })
db.users.estimatedDocumentCount()  // 基于元数据，不支持查询条件
// 去重
db.users.distinct("status")
db.users.distinct("tags", { age: { $gte: 25 } })
```

#### 正则表达式查询

```javascript
// 模糊匹配
db.users.find({ name: /张/ })                   // 包含"张"
db.users.find({ name: /^张/ })                  // 以"张"开头
db.users.find({ email: /@example\.com$/ })      // 以 @example.com 结尾
db.users.find({ name: /三$/i })                  // i 表示不区分大小写
// $regex 操作符
db.users.find({ name: { $regex: "^张", $options: "i" } })
```

#### 高级查询示例

```javascript
// exists：字段是否存在
db.users.find({ email: { $exists: true } })
// type：按 BSON 类型查询
db.users.find({ age: { $type: "int" } })  // 或 { $type: 16 }
// expr：聚合表达式（允许比较同一文档中的两个字段）
db.users.find({ $expr: { $gt: ["$age", 30] } })
// text：全文搜索（需要创建文本索引）
db.articles.createIndex({ title: "text", content: "text" })
db.articles.find({ $text: { $search: "MongoDB 查询" } })
// where：JavaScript 表达式（性能差，避免生产使用）
db.users.find({ $where: "this.age > 25 && this.tags.length > 1" })
```

### 5.3 更新文档

#### 更新操作符

```javascript
// ===== 字段操作符 =====
// $set：设置字段值（字段不存在则创建）
db.users.updateOne(
    { _id: ObjectId("...") },
    { $set: { age: 29, status: "active" } }
)
// $unset：删除字段
db.users.updateOne(
    { _id: ObjectId("...") },
    { $unset: { tempField: "" } }
)
// $rename：重命名字段
db.users.updateMany(
    {},
    { $rename: { "oldFieldName": "newFieldName" } }
)
// $inc：数值自增/自减
db.users.updateOne(
    { name: "张三" },
    { $inc: { age: 1, loginCount: 1 } }  // 自增
)
// $mul：数值乘法
db.users.updateOne(
    { name: "张三" },
    { $mul: { score: 1.1 } }  // 乘以 1.1
)
// $min / $max：只在更小/更大时更新
db.users.updateOne(
    { name: "张三" },
    { $min: { highScore: 500 } }  // 新值小于当前值时才更新
)
// $currentDate：设为当前时间
db.users.updateOne(
    { name: "张三" },
    { $currentDate: { lastModified: true } }
)
// ===== 数组操作符 =====
// $push：向数组追加元素
db.users.updateOne(
    { name: "张三" },
    { $push: { tags: "运维" } }
)
// $push + $each：批量追加
db.users.updateOne(
    { name: "张三" },
    { $push: { tags: { $each: ["运维", "DBA"], $sort: 1 } } }
)
// $addToSet：去重追加（元素不存在才添加）
db.users.updateOne(
    { name: "张三" },
    { $addToSet: { tags: "运维" } }  // 如果"运维"已存在则不添加
)
// $pull：移除匹配的数组元素
db.users.updateOne(
    { name: "张三" },
    { $pull: { tags: "运维" } }
)
// $pullAll：移除所有指定值
db.users.updateOne(
    { name: "张三" },
    { $pullAll: { tags: ["运维", "DBA"] } }
)
// $pop：移除第一个(-1)或最后一个(1)元素
db.users.updateOne(
    { name: "张三" },
    { $pop: { tags: -1 } }  // 移除第一个
)
// 按位置更新数组元素
db.users.updateOne(
    { name: "张三" },
    { $set: { "tags.0": "全栈" } }  // 更新第一个元素
)
// $[]：更新数组所有元素
db.users.updateMany(
    { },
    { $set: { "scores.$[]": 0 } }  // 所有 scores 元素都设为 0
)
```

#### 更新选项

```javascript
// updateOne：更新匹配的第一条
db.users.updateOne(
    { status: "active" },
    { $set: { lastActive: new Date() } }
)
// updateMany：更新所有匹配的
db.users.updateMany(
    { status: "inactive" },
    { $set: { status: "archived" } }
)
// upsert：存在则更新，不存在则插入
db.users.updateOne(
    { email: "new@example.com" },
    { $set: { name: "新人", age: 22, status: "active" } },
    { upsert: true }
)
// replaceOne：完整替换文档（除 _id 外）
db.users.replaceOne(
    { name: "张三" },
    {
        name: "张三",
        age: 30,
        email: "new_email@example.com",
        status: "active"
    }
)
// findAndModify：原子性查找并修改
const result = db.users.findOneAndUpdate(
    { status: "pending" },
    { $set: { status: "processing" } },
    { sort: { createdAt: 1 }, returnDocument: "after" }
)
```

### 5.4 删除文档

```javascript
// 删除匹配的第一条
db.users.deleteOne({ status: "inactive" })
// 删除所有匹配的
db.users.deleteMany({ status: "archived" })
// 删除集合中所有文档（保留集合和索引）
db.users.deleteMany({})
// 删除整个集合（包括索引，比 deleteMany({}) 快）
db.users.drop()
// 条件删除示例
db.users.deleteMany({
    status: "inactive",
    lastLogin: { $lt: new Date("2025-01-01") }
})
```

---

## 6. 索引

### 6.1 索引基础

```javascript
// 创建单字段索引
db.users.createIndex({ email: 1 })  // 1: 升序
// 创建复合索引
db.users.createIndex({ status: 1, age: -1 })
// 创建唯一索引
db.users.createIndex({ email: 1 }, { unique: true })
// 创建稀疏索引（不包含该字段的文档不索引）
db.users.createIndex({ nickname: 1 }, { sparse: true })
// 创建 TTL 索引（到期自动删除文档）
db.sessions.createIndex(
    { createdAt: 1 },
    { expireAfterSeconds: 3600 }  // 1 小时后自动删除
)
// 创建文本索引（全文搜索）
db.articles.createIndex({ title: "text", content: "text" })
// 创建地理空间索引
db.places.createIndex({ location: "2dsphere" })
// 创建哈希索引（分片键常用）
db.users.createIndex({ userId: "hashed" })
// 部分索引（仅对满足条件的文档建索引）
db.users.createIndex(
    { email: 1 },
    { partialFilterExpression: { status: "active" } }
)
// 后台创建索引（不阻塞读写）
db.users.createIndex({ age: 1 }, { background: true })
```

### 6.2 索引管理

```javascript
// 查看集合所有索引
db.users.getIndexes()
// 查看索引大小
db.users.totalIndexSize()
// 删除指定索引
db.users.dropIndex("email_1")
// 删除所有非 _id 索引
db.users.dropIndexes()
// 重建索引（碎片整理）
db.users.reIndex()
// 隐藏/显示索引（测试索引影响）
db.users.hideIndex("email_1")
db.users.unhideIndex("email_1")
// 查看查询执行计划
db.users.find({ email: "test@example.com" }).explain("executionStats")
db.users.find({ age: { $gt: 25 } }).explain("allPlansExecution")
```

### 6.3 索引使用建议

```javascript
// ✅ 遵循 ESR 规则（Equality → Sort → Range）
db.users.createIndex({
    status: 1,        // E: 等值查询字段
    createdAt: 1,     // S: 排序字段
    age: 1            // R: 范围查询字段
})
// ✅ 覆盖查询：所有返回字段都在索引中
// 查询 plan 显示 "totalDocsExamined": 0
db.users.createIndex({ email: 1, name: 1 })
db.users.find({ email: "a@b.com" }, { email: 1, name: 1, _id: 0 })
// ❌ 避免低效索引
// 选择性低（如 status 只有 2 个值）
// 没被查询使用的索引
// 过多索引影响写入性能
```

---

## 7. 聚合管道

### 7.1 常用管道阶段

```javascript
// ===== $match：过滤 =====
db.orders.aggregate([
    { $match: { status: "completed" } }
])
// ===== $group：分组统计 =====
db.orders.aggregate([
    {
        $group: {
            _id: "$customerId",           // 按 customerId 分组
            totalAmount: { $sum: "$amount" },
            avgAmount: { $avg: "$amount" },
            count: { $sum: 1 },
            minAmount: { $min: "$amount" },
            maxAmount: { $max: "$amount" },
            firstOrder: { $first: "$createdAt" },
            lastOrder: { $last: "$createdAt" }
        }
    }
])
// ===== $project：字段投影/计算 =====
db.orders.aggregate([
    {
        $project: {
            customerId: 1,
            amount: 1,
            taxAmount: { $multiply: ["$amount", 0.13] },
            fullName: { $concat: ["$firstName", " ", "$lastName"] },
            createdAt: {
                $dateToString: { format: "%Y-%m-%d", date: "$createdAt" }
            }
        }
    }
])
// ===== $sort：排序 =====
db.orders.aggregate([
    { $sort: { totalAmount: -1 } }
])
// ===== $limit / $skip：分页 =====
db.orders.aggregate([
    { $sort: { createdAt: -1 } },
    { $skip: 0 },
    { $limit: 10 }
])
// ===== $lookup：关联查询 (LEFT JOIN) =====
db.orders.aggregate([
    {
        $lookup: {
            from: "customers",
            localField: "customerId",
            foreignField: "_id",
            as: "customer"
        }
    },
    { $unwind: "$customer" }  // 展开数组
])
// ===== $unwind：展开数组 =====
db.users.aggregate([
    { $unwind: "$tags" },
    { $group: { _id: "$tags", count: { $sum: 1 } } }
])
```

### 7.2 完整数据分析示例

```javascript
// 统计各状态订单的销售总额和平均金额
db.orders.aggregate([
    // 1. 过滤
    { $match: { createdAt: { $gte: new Date("2026-01-01") } } },
    // 2. 关联客户信息
    {
        $lookup: {
            from: "customers",
            localField: "customerId",
            foreignField: "_id",
            as: "customer"
        }
    },
    { $unwind: "$customer" },
    // 3. 分组统计
    {
        $group: {
            _id: "$status",
            totalAmount: { $sum: "$amount" },
            avgAmount: { $avg: "$amount" },
            orderCount: { $sum: 1 },
            customers: { $addToSet: "$customer.name" }
        }
    },
    // 4. 排序
    { $sort: { totalAmount: -1 } },
    // 5. 格式化输出
    {
        $project: {
            _id: 0,
            status: "$_id",
            totalAmount: { $round: ["$totalAmount", 2] },
            avgAmount: { $round: ["$avgAmount", 2] },
            orderCount: 1,
            uniqueCustomerCount: { $size: "$customers" }
        }
    }
])
```

---

## 8. 复制集（Replica Set）

### 8.1 架构概念

```
               ┌──────────────┐
         写    │   Primary    │
     ────────►│   (主节点)    │
               └──┬───┬───┬──┘
         复制     │   │   │   复制
    ┌────────────◄┘   │   └──►┐
    ▼                    ▼
┌──────────┐      ┌──────────┐
│ Secondary │      │ Secondary │
│  (从节点)  │      │  (从节点)  │
└──────────┘      └──────────┘
     ▲                  ▲
     │      读负载       │
     └──────────────────┘
```

- **Primary**：唯一接受写入的节点，将操作记录到 oplog

- **Secondary**：异步复制 Primary 的 oplog，提供读服务

- **Arbiter**（可选）：仅参与选举，不存储数据

- **自动故障转移**：Primary 宕机后，Secondary 自动选举新 Primary（通常 10-30 秒）

### 8.2 部署复制集

```javascript
// ===== 方式一：命令行启动每个节点 =====
// 节点 1 (27017)
mongod --replSet rs0 --port 27017 --dbpath /data/rs0-0 --bind_ip localhost
// 节点 2 (27018)
mongod --replSet rs0 --port 27018 --dbpath /data/rs0-1 --bind_ip localhost
// 节点 3 (27019)
mongod --replSet rs0 --port 27019 --dbpath /data/rs0-2 --bind_ip localhost
// ===== 方式二：配置文件 =====
// mongod.conf
replication:
  replSetName: "rs0"
net:
  port: 27017
  bindIp: 0.0.0.0
  # bindIp: localhost,192.168.1.10
storage:
  dbPath: /data/db
// ===== 初始化复制集 =====
// 连接任一节点后执行
rs.initiate({
    _id: "rs0",
    members: [
        { _id: 0, host: "mongo1:27017", priority: 2 },
        { _id: 1, host: "mongo2:27017", priority: 1 },
        { _id: 2, host: "mongo3:27017", priority: 1, arbiterOnly: true }
    ]
})
```

### 8.3 复制集管理

```javascript
// 查看复制集状态
rs.status()
// 查看复制集配置
rs.conf()
// 查看当前节点是否是 Primary
rs.isMaster()
// 查看 oplog 信息
rs.printReplicationInfo()
// 查看从节点复制延迟
rs.printSecondaryReplicationInfo()
// 手动降级 Primary（让出主节点）
rs.stepDown(60)  // 60 秒内不参与选举
// 添加/移除节点
rs.add("mongo4:27017")
rs.addArb("mongo5:27017")
rs.remove("mongo3:27017")
// 冻结节点（不参与选举）
rs.freeze(120)  // 冻结 120 秒
// 设置从节点隐藏
let cfg = rs.conf()
cfg.members[1].hidden = true   // 对客户端不可见
cfg.members[1].priority = 0    // 永不被选为 Primary
rs.reconfig(cfg)
```

### 8.4 读写关注（Read/Write Concern）

```javascript
// 读关注（读取数据的一致性级别）
db.collection.find().readConcern("local")       // 默认，读当前节点最新
db.collection.find().readConcern("majority")    // 多数节点已确认的数据
db.collection.find().readConcern("linearizable") // 线性一致性（最强）
// 写关注（写入确认级别）
db.collection.insertOne({...}, {
    writeConcern: { w: "majority", j: true, wtimeout: 5000 }
})
// w: 0 — 不等待确认（最快，可能丢数据）
// w: 1 — 默认，Primary 确认
// w: "majority" — 多数节点确认（推荐）
// j: true — 写入磁盘日志后确认
// 读偏好（从哪里读）
db.collection.find().readPref("primary")            // 仅从 Primary 读
db.collection.find().readPref("primaryPreferred")   // 优先 Primary
db.collection.find().readPref("secondary")          // 仅从 Secondary 读
db.collection.find().readPref("secondaryPreferred") // 优先 Secondary
db.collection.find().readPref("nearest")            // 延迟最低的节点
```

---

## 9. 分片集群（Sharding）

### 9.1 架构概览

```
                 ┌─────────────┐
     请求 ──────►│   mongos    │ (路由节点)
                 │  (Router)   │
                 └──────┬──────┘
                        │ 查询 Config Server
           ┌────────────┼────────────┐
           ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  Shard 1 │ │  Shard 2 │ │  Shard 3 │
    │ (复制集)  │ │ (复制集)  │ │ (复制集)  │
    └──────────┘ └──────────┘ └──────────┘
    ┌─────────────────────────────────────┐
    │       Config Server Replica Set     │
    │        (存储集群元数据+分片规则)      │
    └─────────────────────────────────────┘
```

| 组件 | 作用 | 推荐数量 |
| --- | --- | --- |
| **mongos** | 路由节点，接收客户端请求，分发到对应分片 | 2+（无状态） |
| **Config Server** | 存储集群元数据、分片键范围映射 | 3（复制集） |
| **Shard** | 实际存储数据的复制集，每个分片是一个复制集 | 2+ |

### 9.2 部署分片集群

```bash
# ===== 1. 启动 Config Server 复制集 =====
mongod --configsvr --replSet configReplSet --port 27019 --dbpath /data/config
# 初始化
mongosh --port 27019
rs.initiate({
    _id: "configReplSet",
    configsvr: true,
    members: [
        { _id: 0, host: "host1:27019" },
        { _id: 1, host: "host2:27019" },
        { _id: 2, host: "host3:27019" }
    ]
})
# ===== 2. 启动 Shard 复制集 =====
# Shard 1
mongod --shardsvr --replSet shard1 --port 27018 --dbpath /data/shard1
# Shard 2
mongod --shardsvr --replSet shard2 --port 27028 --dbpath /data/shard2
# 初始化每个 shard 的复制集
mongosh --port 27018
rs.initiate({ _id: "shard1", members: [{ _id: 0, host: "host1:27018" }] })
# ===== 3. 启动 mongos 路由 =====
mongos --configdb configReplSet/host1:27019,host2:27019,host3:27019 --port 27017
# ===== 4. 添加分片（连接 mongos 操作）=====
mongosh --port 27017
sh.addShard("shard1/host1:27018")
sh.addShard("shard2/host1:27028")
```

### 9.3 分片策略

#### 范围分片（Range Sharding）

```javascript
// 按字段值的范围分片，适合范围查询
sh.shardCollection("mydb.users", { age: 1 })
// 数据分布示例：
// Shard 1: age [0, 25)
// Shard 2: age [25, 50)
// Shard 3: age [50, ∞)
```

#### 哈希分片（Hash Sharding）

```javascript
// 按字段哈希值均匀分布，适合等值查询
sh.shardCollection("mydb.users", { userId: "hashed" })
// 数据分布：哈希值均匀散布到各分片
// 优点：写入和单条读取均匀分布
// 缺点：范围查询需要广播到所有分片
```

#### 复合分片键

```javascript
// 复合分片键
sh.shardCollection("mydb.orders", { customerId: 1, orderDate: 1 })
// 区域分片（Zone Sharding）
// 为分片添加标签
sh.addShardTag("shard1", "BJ")
sh.addShardTag("shard2", "SH")
// 定义数据范围与标签的对应关系
sh.addTagRange(
    "mydb.users",
    { region: "北京" },
    { region: "北京" },
    "BJ"
)
```

### 9.4 分片集群管理

```javascript
// 启用数据库分片
sh.enableSharding("mydb")
// 对集合启用分片
sh.shardCollection("mydb.users", { userId: "hashed" })
// 查看分片状态
sh.status()
// 查看分片分布
db.users.getShardDistribution()
// 分割 chunk（手动平衡）
sh.splitAt("mydb.users", { userId: 1000 })
// 迁移 chunk
sh.moveChunk("mydb.users", { userId: 1000 }, "shard2")
// 均衡器管理
sh.startBalancer()
sh.stopBalancer()
sh.getBalancerState()
sh.setBalancerState(true)
// 设置均衡窗口（业务低峰期）
db.adminCommand({
    configureCollectionBalancing: "mydb.largeCollection",
    balancerWindow: { from: "02:00", to: "06:00" }
})
// 查看 balancer 状态
sh.isBalancerRunning()
// 均衡器配置
use config
db.settings.updateOne(
    { _id: "balancer" },
    {
        $set: {
            activeWindow: { from: "02:00", to: "06:00" }  // 凌晨 2-6 点
        }
    },
    { upsert: true }
)
```

### 9.5 分片键选择原则

| 原则 | 说明 |
| --- | --- |
| **高基数** | 分片键应有大量唯一值，便于均匀分布 |
| **低频率** | 分片键不应集中在少量值上（避免 hot chunk） |
| **单调递增风险** | 如 `ObjectId`、时间戳，会导致写入集中到一个分片 |
| **查询模式匹配** | 分片键应覆盖大多数查询条件，避免广播查询 |

```javascript
// ✅ 好的分片键
sh.shardCollection("mydb.ecommerce", { userId: "hashed" })  // 均匀分布
// ❌ 坏的分片键
sh.shardCollection("mydb.logs", { logLevel: 1 })           // 基数太低
sh.shardCollection("mydb.events", { timestamp: 1 })         // 单调递增
// ✅ 改进单调递增问题：结合高基数字段
sh.shardCollection("mydb.events", { timestamp: 1, deviceId: 1 })
```

---

## 10. 常用命令速查

### 监控与诊断

```javascript
// 服务器状态
db.serverStatus()
// 当前操作（正在执行的请求）
db.currentOp()
db.currentOp({ active: true, secs_running: { $gt: 3 } })  // 运行超过 3 秒
// 终止操作
db.killOp(opid)
// 慢查询配置
db.setProfilingLevel(1, { slowms: 100 })  // 开启分析，记录 >100ms 的查询
db.getProfilingStatus()
db.system.profile.find().sort({ ts: -1 }).limit(5)  // 查看最近的慢查询
// 集合统计
db.collection.stats()
db.collection.dataSize()
// 连接数
db.serverStatus().connections
// 锁信息
db.serverStatus().locks
// 内存使用
db.serverStatus().mem
db.serverStatus().wiredTiger.cache
```

### 用户与权限

```javascript
// 切换至 admin 库
use admin
// 创建超级管理员
db.createUser({
    user: "admin",
    pwd: "password123",
    roles: ["root"]
})
// 创建数据库用户
db.createUser({
    user: "appUser",
    pwd: "password123",
    roles: [
        { role: "readWrite", db: "mydb" },
        { role: "read", db: "analytics" }
    ]
})
// 查看用户
db.getUsers()
// 修改密码
db.changeUserPassword("appUser", "newPassword")
// 删除用户
db.dropUser("appUser")
```

### 备份与恢复

```bash
# 导出单集合（BSON）
mongodump --db mydb --collection users --out /backup/
# 导出单集合（JSON）
mongoexport --db mydb --collection users --out users.json
# 导出带查询条件
mongoexport --db mydb --collection users \
    --query '{"status":"active"}' \
    --fields name,email \
    --out active_users.json
# 恢复数据
mongorestore --db mydb /backup/mydb/
# 恢复指定集合
mongorestore --db mydb --collection users /backup/mydb/users.bson
# 导入 JSON
mongoimport --db mydb --collection users --file users.json
```

---

## 附：常用运算符速查表

### 比较运算符

| 运算符 | 含义 |
| --- | --- |
| `$eq` | 等于 |
| `$ne` | 不等于 |
| `$gt` | 大于 |
| `$gte` | 大于等于 |
| `$lt` | 小于 |
| `$lte` | 小于等于 |
| `$in` | 在指定列表中 |
| `$nin` | 不在指定列表中 |

### 逻辑运算符

| 运算符 | 含义 |
| --- | --- |
| `$and` | 逻辑与 |
| `$or` | 逻辑或 |
| `$nor` | 逻辑非或 |
| `$not` | 逻辑非 |

### 数组运算符

| 运算符 | 含义 |
| --- | --- |
| `$all` | 包含所有指定元素 |
| `$size` | 数组长度匹配 |
| `$elemMatch` | 至少一个元素满足所有条件 |

### 更新运算符

| 运算符 | 含义 |
| --- | --- |
| `$set` | 设置字段值 |
| `$unset` | 删除字段 |
| `$inc` | 自增/自减 |
| `$push` | 数组追加 |
| `$addToSet` | 数组去重追加 |
| `$pull` | 移除数组元素 |
| `$pop` | 移除首/尾元素 |
