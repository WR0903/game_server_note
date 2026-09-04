## 目录

1. [概述与连接](#1-概述与连接)

2. [常用数据类型及应用场景](#2-常用数据类型及应用场景)

3. [数据类型底层实现原理](#3-数据类型底层实现原理)

   - [SDS（简单动态字符串）](#31-sds简单动态字符串)

   - [链表与 quicklist](#32-链表与-quicklist)

   - [字典（hashtable）](#33-字典hashtable)

   - [跳跃表（skiplist）](#34-跳跃表skiplist)

   - [整数集合（intset）](#35-整数集合intset)

   - [压缩列表（ziplist）](#36-压缩列表ziplist)

   - [listpack](#37-listpack-redis-70)

   - [各类型编码总结](#38-各类型编码总结)

4. [通用命令](#4-通用命令)

5. [发布订阅与消息队列](#5-发布订阅与消息队列)

6. [事务与 Pipeline](#6-事务与-pipeline)

7. [持久化：RDB 与 AOF](#7-持久化rdb-与-aof)

8. [过期策略与内存淘汰](#8-过期策略与内存淘汰)

9. [主从复制与同步](#9-主从复制与同步)

10. [集群方案：Sentinel 与 Cluster](#10-集群方案sentinel-与-cluster)

11. [分布式锁](#11-分布式锁)

12. [缓存三大问题与解决方案](#12-缓存三大问题与解决方案)

13. [线程模型与高性能原理](#13-线程模型与高性能原理)

14. [常用命令速查](#14-常用命令速查)

---

## 1. 概述与连接

### 1.1 为什么选择 Redis？

传统关系型数据库（如 MySQL）不能适用所有场景，比如秒杀库存扣减容易把数据库打崩，需要引入缓存中间件。市面上常用的缓存中间件有 Redis 和 Memcached：

| 对比 | Redis | Memcached |
| --- | --- | --- |
| 数据结构 | 丰富（String/Hash/List/Set/ZSet...） | 仅 String |
| 持久化 | RDB + AOF | 不支持 |
| 集群 | Sentinel + Cluster | 客户端一致性哈希 |
| 线程模型 | 单线程（6.0+ 多线程 IO） | 多线程 |
| 功能 | 发布订阅、Lua、事务、Stream | 基础 KV |

### 1.2 连接 Redis

```bash
# 命令行连接
redis-cli -h 127.0.0.1 -p 6379 -a password
# 连接后测试
127.0.0.1:6379> PING
PONG
# 选择数据库（默认 0-15，共 16 个）
127.0.0.1:6379> SELECT 1
OK
# 查看信息
127.0.0.1:6379> INFO
127.0.0.1:6379> INFO memory
127.0.0.1:6379> INFO replication
```

**各语言客户端：**

```python
# Python (redis-py)
import redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
r.set('key', 'value')
print(r.get('key'))  # 'value'
# 带连接池
pool = redis.ConnectionPool(host='localhost', port=6379, max_connections=100)
r = redis.Redis(connection_pool=pool)
```

```go
// Go (go-redis)
import "github.com/redis/go-redis/v9"
rdb := redis.NewClient(&redis.Options{
    Addr:     "localhost:6379",
    Password: "",
    DB:       0,
})
ctx := context.Background()
rdb.Set(ctx, "key", "value", 0)
val := rdb.Get(ctx, "key").Val()  // "value"
```

```javascript
// Node.js (ioredis)
const Redis = require('ioredis');
const redis = new Redis({
    host: 'localhost',
    port: 6379,
    maxRetriesPerRequest: null,
});
await redis.set('key', 'value');
const val = await redis.get('key');  // 'value'
```

---

## 2. 常用数据类型及应用场景

### 2.1 String（字符串）

最基础的类型，普通的 SET / GET 做 **KV 缓存**，也可以做计数器。

```bash
SET article:1000:title "Redis 入门指南"
SET article:1000:views 0
INCR article:1000:views     # → 1
INCRBY article:1000:views 10  # → 11
GET article:1000:views       # → "11"
# 分布式锁（SETNX + EX）
SET lock:order:1001 uuid-value NX EX 30
# 缓存 JSON
SET user:1001 '{"name":"张三","age":28}'
```

**应用场景**：

- **共享 Session**：用户刷新页面不需重新登录，将 Session 集中管理在 Redis 中

- **计数器**：文章阅读量、点赞数、限流计数

- **分布式锁**：SETNX + 过期时间

### 2.2 Hash（哈希）

类似 Map 结构，适合存储对象属性。

```bash
HSET user:1001 name "张三" age 28 email "zhangsan@example.com"
HGET user:1001 name          # "张三"
HGETALL user:1001            # 所有字段
HINCRBY user:1001 age 1      # age + 1
HDEL user:1001 email          # 删除字段
HEXISTS user:1001 phone       # 判断字段是否存在
```

**应用场景**：商品对象（多属性）、用户信息、购物车（field=商品ID, value=数量）

### 2.3 List（列表）

有序列表，底层是双向链表，可从两端操作。

```bash
LPUSH queue:tasks "task1" "task2" "task3"   # 左插入
RPUSH queue:tasks "task4"                     # 右插入
LPOP queue:tasks                              # 左弹出 → "task3"
RPOP queue:tasks                              # 右弹出 → "task4"
LRANGE queue:tasks 0 -1                       # 获取全部
# 阻塞弹出（做消息队列）
BLPOP queue:tasks 30   # 30 秒超时，无消息时阻塞
# 裁剪列表（保留最新 100 条）
LTRIM news:latest 0 99
```

**应用场景**：消息队列、最新动态列表、粉丝列表、文章评论列表

### 2.4 Set（集合）

无序集合，自动去重，支持集合运算。

```bash
SADD user:1:friends "user2" "user3" "user4"
SADD user:2:friends "user1" "user3" "user5"
# 交集 → 共同好友
SINTER user:1:friends user:2:friends   # → "user3"
# 差集 → 我有的你没有
SDIFF user:1:friends user:2:friends    # → "user2" "user4"
# 并集 → 所有好友
SUNION user:1:friends user:2:friends
SISMEMBER user:1:friends "user5"       # 判断是否存在
SCARD user:1:friends                   # 集合大小
```

**应用场景**：共同好友、用户标签、抽奖（SPOP 随机弹出）、点赞用户集合

### 2.5 Sorted Set（有序集合）

去重且排序，写入时指定分数（score），自动按分数排序。

```bash
ZADD leaderboard 100 "player1" 200 "player2" 150 "player3"
# 按分数升序排名
ZRANGE leaderboard 0 -1 WITHSCORES
# 按分数降序排名（排行榜）
ZREVRANGE leaderboard 0 2 WITHSCORES
# 获取分数范围
ZRANGEBYSCORE leaderboard 100 200 WITHSCORES
# 获取 player2 的排名
ZRANK leaderboard "player2"      # 升序排名
ZREVRANK leaderboard "player2"   # 降序排名
# 增加分数
ZINCRBY leaderboard 50 "player1"
```

**应用场景**：排行榜（游戏、电商销量）、延时队列（score=时间戳）、带权重的任务队列

### 2.6 其他高级类型

| 类型 | 说明 | 常用命令 |
| --- | --- | --- |
| **HyperLogLog** | 基数统计，12KB 可统计 2^64 个 | `PFADD`, `PFCOUNT` |
| **Geo** | 地理位置 | `GEOADD`, `GEORADIUS`, `GEODIST`, `GEOPOS` |
| **Bitmap** | 位图 | `SETBIT`, `GETBIT`, `BITCOUNT`, `BITOP` |
| **Bloom Filter** | 布隆过滤器（需 RedisBloom 模块） | `BF.ADD`, `BF.EXISTS` |
| **Stream** | 5.0+ 持久化消息队列 | `XADD`, `XREAD`, `XGROUP` |

---

## 3. 数据类型底层实现原理

> Redis 为每种类型设计了多种底层编码，会根据数据大小自动切换，在**空间效率**和**时间效率**之间取平衡。

### 3.1 SDS（简单动态字符串）

**Redis 的 String 类型底层使用 SDS（Simple Dynamic String），而非 C 原生字符串。**

```c
struct sdshdr {
    int len;    // 已使用长度
    int free;   // 剩余可用空间
    char buf[]; // 字符数组（柔性数组）
};
```

**SDS vs C 字符串：**

| 对比 | C 字符串 | SDS |
| --- | --- | --- |
| 获取长度 | O(n) 遍历 | O(1) 直接读 `len` |
| 缓冲区溢出 | 可能溢出 | 自动扩容，安全 |
| 内存分配 | 每次修改必重分配 | 预分配 + 惰性释放 |
| 二进制安全 | ❌（遇 `\0` 截断） | ✅（用 `len` 判断结束） |
| 兼容性 | — | 兼容部分 C 字符串 API |

**扩容策略**：

- 当 `len < 1MB` 时，预分配 `len` 长度的空闲空间（总容量 = len × 2）

- 当 `len >= 1MB` 时，预分配 1MB 空闲空间

**内存回收**：缩短字符串时不会立即释放内存，`free` 记录空闲量，有需要时再使用。

**二进制安全示例**：SDS 不依赖 `\0` 判断结尾，而是根据 `len` 读取，所以可以存储图片、音频等二进制数据。

```
C 字符串：  "hello\0world"  → 读到 \0 截断，得到 "hello"
SDS：       len=11, buf="hello\0world"  → 正确读取完整 11 字节
```

### 3.2 链表与 quicklist

#### 早期双向链表（Redis 3.2 之前）

```c
typedef struct listNode {
    struct listNode *prev;
    struct listNode *next;
    void *value;
} listNode;
typedef struct list {
    listNode *head;
    listNode *tail;
    unsigned long len;       // 节点数
    void *(*dup)(void *ptr);  // 复制函数
    void (*free)(void *ptr);  // 释放函数
    int (*match)(void *ptr, void *key);  // 匹配函数
} list;
```

**特点**：双端、无环、带头尾指针和长度计数器，支持多态（不同值类型）。

**缺点**：每个节点独立分配内存，内存不连续，内存碎片多，指针占用空间大。

#### quicklist（Redis 3.2+）

**quicklist 将 adlist 和 ziplist 结合**：整体是双向链表，每个节点是一个 ziplist。

```
quicklist:
┌─────────┐     ┌─────────┐     ┌─────────┐
│ ziplist │ ←→ │ ziplist │ ←→ │ ziplist │
│ (多元素) │     │ (多元素) │     │ (多元素) │
└─────────┘     └─────────┘     └─────────┘
```

```c
typedef struct quicklist {
    quicklistNode *head;
    quicklistNode *tail;
    unsigned long count;     // 所有 ziplist 中元素总数
    unsigned long len;        // quicklistNode 数量
    int fill : QL_FILL_BITS;  // 每个 ziplist 最大容量
    ...
} quicklist;
typedef struct quicklistNode {
    struct quicklistNode *prev;
    struct quicklistNode *next;
    unsigned char *zl;        // 指向 ziplist
    unsigned int sz;          // ziplist 字节数
    unsigned int count : 16;  // ziplist 中的元素数
    ...
} quicklistNode;
```

**优点**：

- 兼具链表灵活插入和 ziplist 空间紧凑的优势

- `fill` 参数控制每个节点 ziplist 的大小，可根据场景调整（正数=元素个数上限，负数=内存上限）

### 3.3 字典（hashtable）

**Hash 类型和所有 Key-Value 数据库本身都使用字典实现。**

```c
typedef struct dict {
    dictType *type;      // 类型特定函数
    void *privdata;      // 私有数据
    dictht ht[2];        // 两个哈希表（用于渐进式 rehash）
    long rehashidx;      // rehash 进度，-1 表示没有进行
    int16_t pauserehash; // 暂停 rehash 标记
} dict;
typedef struct dictht {
    dictEntry **table;      // 哈希表数组
    unsigned long size;     // 哈希表大小（2^n）
    unsigned long sizemask; // size - 1（位运算代替取模）
    unsigned long used;     // 已有节点数
} dictht;
typedef struct dictEntry {
    void *key;
    union { void *val; uint64_t u64; int64_t s64; } v;
    struct dictEntry *next;  // 链地址法解决冲突
} dictEntry;
```

#### 哈希算法与冲突解决

```
# 键的哈希计算
hash = dictType->hashFunction(key);    # 如 MurmurHash2
index = hash & dict->ht[0].sizemask;   # 位运算取模
# 冲突解决：链地址法
# 新节点插入链表头部（O(1)，不需要遍历尾部）
```

```
table[index]:
┌───┐     ┌─────────┐    ┌─────────┐
│ ●─┼────→│ dictEntry│───→│ dictEntry│───→ NULL
└───┘     │ key1:v1  │    │ key2:v2  │
          └─────────┘    └─────────┘
```

#### 渐进式 rehash

**为什么需要？** 哈希表负载因子过高/过低时需扩容/缩容，若一次性迁移所有数据会阻塞服务。

**过程**：

```
1. 触发条件：
   - 扩容：used / size >= 1（且无 BGSAVE）或 >= 5
   - 缩容：used / size <= 0.1
   - 扩容后大小 = 第一个 >= used * 2 的 2^n
   - 缩容后大小 = 第一个 >= used 的 2^n
2. 渐进式迁移：
   ┌──────┐  ┌──────┐
   │ ht[0]│  │ ht[1]│     ← 分配新表，设置 rehashidx = 0
   └──────┘  └──────┘
   旧数据     空表
3. 每次对字典的增删查改操作，顺带迁移 ht[0] 中 rehashidx 索引上的
   链表到 ht[1]，迁移完成后 rehashidx++
4. rehash 期间：
   - 查询：先查 ht[0]，没找到再查 ht[1]
   - 新增：直接写入 ht[1]
   - 删除：两个表都尝试删除
5. 当 ht[0] 中的全部数据迁移完毕，rehashidx = -1，
   将 ht[1] 设为 ht[0]，ht[1] 设为空表，完成。
```

### 3.4 跳跃表（skiplist）

**Sorted Set 的底层实现之一**，通过多层索引加速查找。

```
查找 50 的过程（O(log n)）：
level 3: [1] ─────────────────────────────────→ [120]        ← 最高层
level 2: [1] ───────────→ [35] ────────────────→ [120]
level 1: [1] → [10] → [35] → [48] → [50] → [87] → [120]    ← 原始链表
level 0: [1] → [10] → [35] → [48] → [50] → [87] → [120] → [NULL]
步骤：
  1. 从 level 3 的 1 出发，下一跳 120 > 50，下降
  2. level 2 的 1 → 35，下一跳 120 > 50，下降
  3. level 1 的 35 → 48，下一跳 50，命中！
  共 4 步，比原始链表的 5 步还少（数据量大时差异更大）
```

```c
typedef struct zskiplistNode {
    sds ele;                          // 成员（member）
    double score;                     // 分值
    struct zskiplistNode *backward;   // 后退指针
    struct zskiplistLevel {
        struct zskiplistNode *forward; // 前进指针
        unsigned long span;            // 跨度（该层到下一个节点的距离）
    } level[];                        // 柔性数组，多层索引
} zskiplistNode;
typedef struct zskiplist {
    struct zskiplistNode *header, *tail;
    unsigned long length;             // 节点数
    int level;                        // 最大层数（不含表头）
} zskiplist;
```

**层数生成**：随机算法，每次生成新节点时，有 `1/4` 概率增加一层（power law 分布，最大 64 层，Redis 7.0 改为 32 层）。

```
P(level=1) = 3/4
P(level=2) = 3/16
P(level=3) = 3/64
P(level≥k) = (1/4)^(k-1)  → 越高层越稀疏
```

**skiplist vs 平衡树：**

| 对比 | 跳表 | 平衡树 |
| --- | --- | --- |
| 实现复杂度 | 简单 | 复杂（旋转、染色） |
| 范围查找 | 天然支持（正向遍历） | 需中序遍历 |
| 插入删除 | 只需改相邻节点 | 需要旋转平衡 |
| 并发 | 容易加锁（局部修改） | 锁粒度难以控制 |

### 3.5 整数集合（intset）

**Set 的底层实现之一**，当集合全为整数且数量较少时使用。比 hashtable 更省内存。

```c
typedef struct intset {
    uint32_t encoding;   // INTSET_ENC_INT16 / INT32 / INT64
    uint32_t length;     // 元素个数
    int8_t contents[];   // 实际数组，从小到大有序排列
} intset;
```

**特点**：

- 元素有序（二分查找 O(log n)）

- 不重复（插入时先二分查找是否存在）

- **自动升级**：插入更大的整数时，自动升级整个数组的编码宽度

```
初始：INTSET_ENC_INT16, contents = [1, 3, 5, 7]（每个 16 位）
插入 65536（超出 int16 范围）：
1. 将编码升级为 INTSET_ENC_INT32
2. 扩展数组空间（从 4×16bit → 5×32bit）
3. 重置所有元素位置
4. 插入 65536：contents = [1, 3, 5, 7, 65536]
注意：编码只能升级，不能降级！
```

### 3.6 压缩列表（ziplist）

**Hash / List / ZSet 在数据较少时使用的紧凑存储结构。** 一块连续内存，无指针开销。

```
ziplist 内存布局：
┌────────┬──────┬──────┬──────┬─────┬──────┬────────┐
│zlbytes │zltail│zllen │entry1│entry2│...  │zlend   │
│ 总字节数 │尾偏移 │节点数 │      │      │     │ 结束标记 │
│ 4B     │ 4B   │ 2B   │      │      │     │ 1B(255)│
└────────┴──────┴──────┴──────┴─────┴──────┴────────┘
entry 结构：
┌───────────────────┬──────────┬──────────┐
│ prevlen           │ encoding │ data     │
│ 前一个节点的长度     │ 编码类型  │ 实际数据  │
└───────────────────┴──────────┴──────────┘
prevlen：前一个 entry 的长度
  - 若前节点长度 < 254 字节，prevlen 占 1 字节
  - 若前节点长度 >= 254 字节，prevlen 占 5 字节（首字节 254 + 4 字节长度）
```

**优点**：连续内存，无指针，节省空间。

**缺点**：**连锁更新问题**。

```
连锁更新场景：
  有多个长度 253 字节的节点（每个 prevlen 是 1 字节）：
  [entry1:253B] [entry2:253B] [entry3:253B] ...
  在头部插入 254+ 字节的新节点：
  [new:300B] [entry1:253B] [entry2:253B] ...
  问题：
  1. entry1 的 prevlen 需要从 1B 变成 5B（记录 new 的 300B）
  2. entry1 从 253B → 257B，导致 entry2 的 prevlen 也要从 1B 变 5B
  3. entry2 从 253B → 257B，导致 entry3 的 prevlen 也要变...
  4. 产生链式反应！
  后果：最坏情况下需要 O(N²) 次内存重分配，但实际触发条件苛刻
        （需要大批量连续等长节点恰好卡在 254 边界）
```

### 3.7 listpack（Redis 7.0+）

**替代 ziplist**，解决连锁更新问题。

```
listpack entry 结构：
┌───────────┬──────────┬──────────┬──────────┐
│ encoding  │ data     │ backlen  │
│ 编码类型   │ 实际数据  │ 本节点长度 │
└───────────┴──────────┴──────────┘
关键区别：记录的是本节点长度（backlen），而非前节点长度（prevlen）
- 读取前一个节点时，用当前节点指针减去 backlen 计算得到
- 每个 entry 独立，修改一个不会影响其他 entry 的 prevlen 字段
- 彻底避免了连锁更新！
```

### 3.8 各类型编码总结

| 类型 | 编码 | 触发条件 |
| --- | --- | --- |
| **String** | `embstr` | 长度 ≤ 44 字节（一次分配，只读） |
| | `raw` | 长度 > 44 字节（两次分配，可修改） |
| | `int` | 值为整数 |
| **Hash** | `listpack`（7.0+）/ `ziplist` | 字段数 ≤ 512 且所有字段和值长度 ≤ 64B |
| | `hashtable` | 超过 ziplist/listpack 阈值 |
| **List** | `quicklist` | 3.2+ 统一使用 quicklist |
| **Set** | `intset` | 全整数且元素数 ≤ 512 |
| | `hashtable` | 超过 intset 阈值或包含非整数 |
| **ZSet** | `listpack`（7.0+）/ `ziplist` | 元素数 ≤ 128 且所有成员长度 ≤ 64B |
| | `skiplist + dict` | 超过 ziplist/listpack 阈值 |

**ZSet 为什么同时用 skiplist 和 dict？**

```
skiplist：按 score 排序，做范围查询（ZRANGE、ZRANK 等）
dict：    按 member 查 score（O(1)），如 ZSCORE
两者共享同一份 member 和 score（通过指针），不会两份数据。
```

**编码查看**：

```bash
OBJECT ENCODING user:1001     # 查看 key 的底层编码
```

**阈值调整**（redis.conf）：

```
hash-max-listpack-entries 512    # Hash 转 hashtable 的 entry 数阈值
hash-max-listpack-value 64       # Hash 转 hashtable 的单值字节阈值
zset-max-listpack-entries 128
zset-max-listpack-value 64
set-max-intset-entries 512
```

---

## 4. 通用命令

```bash
# Key 操作
KEYS pattern        # 查找 key（生产慎用，可用 SCAN 代替）
SCAN 0 MATCH user:* COUNT 100  # 游标迭代，可能返回重复
EXISTS key1 key2    # 判断 key 是否存在
TYPE key            # 查看类型
EXPIRE key 3600     # 设置过期时间（秒）
EXPIREAT key 1672500000  # 设置过期时间戳
TTL key             # 查看剩余时间（-1 永不过期，-2 已过期）
PERSIST key         # 移除过期时间，永久保存
DEL key1 key2       # 删除
RENAME old new      # 重命名（可能覆盖）
RENAMENX old new    # 仅 new 不存在时重命名
# 批量操作
MGET key1 key2 key3
MSET key1 "v1" key2 "v2" key3 "v3"
```

---

## 5. 发布订阅与消息队列

### 5.1 Pub/Sub（发布订阅）

```bash
# 客户端 A：订阅频道
SUBSCRIBE channel:news
PSUBSCRIBE channel:*     # 模式订阅
# 客户端 B：发布消息
PUBLISH channel:news "新消息"
```

**特点**：

- 1:N 消息队列模式

- **消费者下线期间的消息会丢失**（不持久化）

- 适合实时性高的场景（如 WebSocket 推送），不适合重要消息

### 5.2 List 做消息队列

```bash
# 生产者
RPUSH mq:tasks "{\"task\":\"send_email\",\"user_id\":1}"
# 消费者（阻塞式，推荐用 BLPOP）
BLPOP mq:tasks 30   # 超时 30 秒
# 消费者（非阻塞，需轮询 + sleep）
LPOP mq:tasks
```

**优点**：无消息时 BLPOP 阻塞不占 CPU。

**缺点**：消费确认弱、不支持重复消费、无消费者组。

### 5.3 延时队列

使用 Sorted Set 实现，score 为执行时间戳。

```bash
# 生产延时消息（5 秒后执行）
ZADD delay:queue $(date +%s -d '+5 seconds') "msg:{user:1}"
# 消费（取当前时间之前的第一条）
ZRANGEBYSCORE delay:queue 0 $(date +%s) LIMIT 0 1
# 消费后移除
ZREMRANGEBYRANK delay:queue 0 0
```

```
轮询流程：
  1. ZRANGEBYSCORE 取当前时间之前的数据
  2. 处理数据
  3. ZREM 删除已处理的消息
  4. 若有多个消费者，使用 ZPOPMIN（5.0+）来原子性地消费
```

### 5.4 Stream（5.0+，推荐）

```bash
# 生产消息
XADD mystream * field1 value1 field2 value2  # * = 自动生成 ID
# 消费消息（从头开始）
XREAD COUNT 2 STREAMS mystream 0
# 消费者组
XGROUP CREATE mystream mygroup $ MKSTREAM   # 创建组（从末尾开始）
XREADGROUP GROUP mygroup consumer1 COUNT 1 STREAMS mystream >
# 消费后需确认
XACK mystream mygroup 消息ID
```

---

## 6. 事务与 Pipeline

### 6.1 事务

```bash
MULTI              # 开启事务
SET key1 "val1"
INCR counter
GET key1
EXEC               # 提交执行
# 放弃事务
MULTI
SET key2 "val2"
DISCARD            # 取消事务，所有命令不执行
```

**Redis 事务特点**：

- 不支持回滚（某条命令失败不影响其他命令）

- 无隔离级别（单线程，天然串行）

- `WATCH key` 可实现乐观锁

```bash
# 乐观锁：WATCH + MULTI
WATCH mykey
val = GET mykey
MULTI
SET mykey val + 100
EXEC
# 若 WATCH 期间 mykey 被修改，EXEC 返回 nil
```

### 6.2 Pipeline（管道）

将多个命令打包发送，减少 RTT（往返时间）。

```python
# Python
pipe = r.pipeline()
pipe.set('key1', 'val1')
pipe.set('key2', 'val2')
pipe.incr('counter')
pipe.get('key1')
results = pipe.execute()  # 一次发送，批量返回
```

```go
// Go
pipe := rdb.Pipeline()
pipe.Set(ctx, "key1", "val1", 0)
pipe.Set(ctx, "key2", "val2", 0)
pipe.Incr(ctx, "counter")
cmds, _ := pipe.Exec(ctx)
```

```
单条发送：
  Client ──RTT1──→ Server
  Client ←──RTT1── Server
  Client ──RTT2──→ Server   ← 3 个 RTT
  Client ←──RTT2── Server
  Client ──RTT3──→ Server
  Client ←──RTT3── Server
Pipeline：
  Client ─发送3条命令→ Server  ← 1 个 RTT
  Client ←返回3条结果─ Server
```

> Pipeline 内的命令**没有因果关系**要求（不是原子的，中间可能插入其他客户端命令）。

---

## 7. 持久化：RDB 与 AOF

### 7.1 RDB（快照持久化）

**定时将内存数据生成快照保存到磁盘。** fork 一个子进程，将数据以二进制方式保存为 `.rdb` 文件。

```bash
# 配置（redis.conf）
save 900 1      # 900 秒内至少 1 次修改
save 300 10     # 300 秒内至少 10 次修改
save 60 10000   # 60 秒内至少 10000 次修改
# 手动触发
SAVE            # 主进程阻塞执行（不推荐）
BGSAVE          # fork 子进程异步执行（推荐）
LASTSAVE        # 查看最近一次保存时间
```

**流程**：

```
主进程 fork() → 子进程（共享内存，Copy-on-Write）
  │
  ├─ 主进程继续处理请求（修改页触发 COW 复制）
  │
  └─ 子进程遍历所有键，写入临时 RDB 文件
       └─ 写入完成后替换旧 RDB 文件（原子 rename）
```

**优点**：

- 适合冷备份，可定时同步到远端

- 恢复速度快（直接加载二进制到内存）

- 对主进程影响小（fork 子进程完成）

**缺点**：

- 两次快照之间的数据可能丢失（如 5 分钟间隔丢失 5 分钟数据）

- fork 子进程时，若数据量超大，可能短暂暂停服务

### 7.2 AOF（追加日志持久化）

**将所有写命令以 append-only 方式追加到日志文件。**

```bash
# 配置（redis.conf）
appendonly yes                          # 开启 AOF
appendfsync always                      # 每次写都刷盘（最安全）
appendfsync everysec                    # 每秒刷盘一次（推荐，最多丢 1 秒）
appendfsync no                          # 操作系统决定（最快）
```

**AOF 重写（rewrite）**：AOF 文件会越来越大，需要定期重写以压缩。

```bash
# 自动重写触发条件
auto-aof-rewrite-percentage 100  # 比上次重写后增长 100%
auto-aof-rewrite-min-size 64mb   # AOF 文件最小 64MB
# 手动触发
BGREWRITEAOF
```

```
重写前 AOF：
  SET counter 1
  SET counter 2
  SET counter 3
  SET counter 4    ← 4 条命令
重写后 AOF：
  SET counter 4    ← 压缩为 1 条
```

**优点**：

- 数据安全性高（最多丢 1 秒）

- 日志可读，适合灾难恢复

- append-only 方式，磁盘寻址开销小

**缺点**：

- 同数据量下文件比 RDB 大

- 恢复速度比 RDB 慢（需逐条回放命令）

- QPS 比纯 RDB 低（有 fsync 开销）

### 7.3 持久化选择建议

| 场景 | 建议 |
| --- | --- |
| 缓存（数据可重建） | 关闭持久化 |
| 对数据完整性要求高 | **RDB + AOF 同时开启** |
| 可接受少量数据丢失 | 仅 RDB |
| 追求数据最安全 | 仅 AOF (everysec) |

> **推荐方案**：同时开启。真出问题时先用 RDB 快速恢复，再回放 AOF 补全最近数据。

### 7.4 AOF vs RDB 对比

| 对比 | RDB | AOF |
| --- | --- | --- |
| 启动优先级 | 低（AOF 优先） | 高 |
| 文件大小 | 小（压缩二进制） | 大（文本命令） |
| 恢复速度 | 快 | 慢 |
| 数据安全 | 可能丢几分钟 | 最多丢 1 秒 |
| 写入性能影响 | 小 | 大（fsync） |
| 适用场景 | 冷备 | 热备 |

---

## 8. 过期策略与内存淘汰

### 8.1 过期键删除策略

Redis 采用 **定期删除 + 惰性删除** 组合策略。

**定期删除**：默认每 100ms 随机抽取一批设置了过期时间的 key 检查并删除。

```
流程：
  1. 每 100ms 执行一次
  2. 从过期字典中随机取 20 个 key
  3. 删除过期的 key
  4. 如果过期比例 > 25%，重复步骤 2-3
  5. 限制每次执行不超过 25ms（防止阻塞主线程）
```

**惰性删除**：访问 key 时检查是否过期，过期则删除并返回空。

```
GET mykey
  → 检查是否过期
  → 过期：删除，返回 nil
  → 未过期：正常返回
```

### 8.2 内存淘汰机制

当内存达到 `maxmemory` 且过期键未被删除时触发：

| 策略 | 行为 |
| --- | --- |
| **noeviction** | 返回错误，不删除任何数据（默认） |
| **allkeys-lru** | 从**所有键**中淘汰最近最少使用的 |
| **volatile-lru** | 从**设置了过期时间的键**中淘汰 LRU |
| **allkeys-lfu** | 从**所有键**中淘汰使用频率最低的 |
| **volatile-lfu** | 从**设置了过期时间的键**中淘汰 LFU |
| **allkeys-random** | 从**所有键**中随机淘汰 |
| **volatile-random** | 从**设置了过期时间的键**中随机淘汰 |
| **volatile-ttl** | 从过期键中淘汰 TTL 最短的 |

```bash
# 配置
maxmemory 2gb
maxmemory-policy allkeys-lru
```

**LRU vs LFU：**

| | LRU（最近最少使用） | LFU（最不经常使用） |
| --- | --- | --- |
| 核心 | 按最后访问时间 | 按访问频率 |
| 问题 | 偶发访问冲高效率 | 历史热点难淘汰 |
| 适用 | 常规业务缓存 | 频率敏感（如推荐系统） |

> Redis 的 LRU 是**近似 LRU**：随机采样 N 个 key，淘汰其中最旧的一个（`maxmemory-samples 5` 控制采样数）。

---

## 9. 主从复制与同步

### 9.1 为什么需要主从架构？

- 单机 QPS 有上限（读写一台机器扛不住）

- 数据冗余备份

- 读写分离（master 写，slave 读）

```
         ┌──────────┐
         │  Master  │ ← 写操作
         └────┬─────┘
       ┌──────┼──────┐
       ▼      ▼      ▼
   ┌──────┐┌──────┐┌──────┐
   │Slave1││Slave2││Slave3│  ← 读操作
   └──────┘└──────┘└──────┘
```

### 9.2 同步过程

```bash
# Slave 连接 Master
SLAVEOF master_ip master_port   # 或 REPLICAOF（5.0+）
```

**全量同步（首次连接）**：

```
Slave                    Master
  │── PSYNC ? -1 ────────→│  (请求全量同步)
  │                        │
  │                        │  1. 执行 BGSAVE，生成 RDB
  │                        │  2. 期间写命令记录到 replication buffer
  │                        │
  │←── 发送 RDB ──────────│
  │                        │
  │  3. 清空旧数据           │
  │  4. 加载 RDB 到内存     │
  │                        │
  │←── 发送 buffer 中的命令 ─│
  │                        │
  │  5. 执行增量命令        │
  │                        │
  │────────────────同步完成─→│
```

**增量同步**（后续断线重连）：

```
Slave                    Master
  │── PSYNC replid offset ─→│
  │                        │
  │    若 offset 在 replication buffer 中 → 发送增量数据
  │    若 offset 不在 → 重新全量同步
  │                        │
  │←── 增量命令 ────────────│
```

**关键概念**：

| 概念 | 说明 |
| --- | --- |
| `repl_backlog_buffer` | 环形缓冲区，记录最近的写命令，默认 1MB |
| `replication id` | 主节点标识，用于判断主节点是否变更 |
| `replication offset` | 复制偏移量，标识同步进度 |

### 9.3 配置示例

```bash
# Master 配置（redis.conf）
# （默认无需特殊配置）
# Slave 配置（redis.conf）
replicaof 192.168.1.100 6379
replica-read-only yes               # 从节点只读
masterauth "master_password"        # 主节点密码
```

---

## 10. 集群方案：Sentinel 与 Cluster

### 10.1 Sentinel（哨兵）

**着眼于高可用**，在 master 宕机时自动将 slave 提升为 master。

```
┌──────────────┐
│   Sentinel 1  │──┐
└──────────────┘  │    ┌──────────┐
                  ├────│  Master   │
┌──────────────┐  │    └────┬─────┘
│   Sentinel 2  │──┤     ┌───┴───┐
└──────────────┘  │   Slave1  Slave2
                  │
┌──────────────┐  │
│   Sentinel 3  │──┘
└──────────────┘
```

**哨兵功能**：

| 功能 | 说明 |
| --- | --- |
| **集群监控** | 监控 master 和 slave 是否正常工作 |
| **消息通知** | 实例故障时通知管理员 |
| **故障转移** | master 挂掉后自动选举新 master |
| **配置中心** | 故障转移后通知 client 新 master 地址 |

```bash
# sentinel.conf
sentinel monitor mymaster 127.0.0.1 6379 2  # 2 个哨兵同意才判定下线
sentinel down-after-milliseconds mymaster 30000
sentinel failover-timeout mymaster 180000
# 启动哨兵
redis-sentinel sentinel.conf
```

> **哨兵必须部署 ≥ 3 个实例**以保证自身高可用。哨兵 + 主从**不能保证数据不丢失**，但可以保证集群高可用。

### 10.2 Cluster（集群）

**着眼于扩展性**，在单机内存不足时进行分片存储。

```
┌──────────────────────────────────────────────┐
│                  Redis Cluster                │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Master 1 │  │ Master 2 │  │ Master 3 │   │
│  │ slot0-   │  │ slot5461-│  │ slot10923│   │
│  │ 5460     │  │ 10922    │  │ -16383   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │         │
│  Slave1A         Slave2A        Slave3A       │
│  Slave1B         Slave2B        Slave3B       │
└──────────────────────────────────────────────┘
16384 个哈希槽（slot）均匀分布在 master 节点中
key → CRC16(key) % 16384 → 路由到对应 master
```

#### 基本操作

```bash
# 创建 Cluster（每个节点执行）
redis-cli --cluster create \
  192.168.1.1:6379 192.168.1.2:6379 192.168.1.3:6379 \
  192.168.1.4:6379 192.168.1.5:6379 192.168.1.6:6379 \
  --cluster-replicas 1   # 每个 master 1 个 slave
# 查看集群状态
redis-cli -c CLUSTER INFO
redis-cli -c CLUSTER NODES
redis-cli -c CLUSTER SLOTS
# 添加节点
redis-cli --cluster add-node 新节点IP:端口 已存在节点IP:端口
redis-cli --cluster add-node 新节点IP:端口 已存在节点IP:端口 --cluster-slave
# 重新分片（迁移 slot）
redis-cli --cluster reshard 目标节点IP:端口
# 访问（客户端必须用 -c 启用集群模式）
redis-cli -c -h 192.168.1.1 -p 6379
```

#### 数据分布方式

**哈希槽分区**：`slot = CRC16(key) % 16384`

```bash
# 计算 key 的 slot
CLUSTER KEYSLOT "user:1001"     # → 返回 slot 编号
# 查看哈希槽（hash tag）：{} 之间的内容参与哈希
# user:{1001}:name 和 user:{1001}:age → 相同 slot（确保多 key 操作）
```

#### 节点间通信

使用 **Gossip 协议**（流言协议）在集群节点间传播信息：

- 每个节点维护一张节点列表

- 周期性（每秒）随机选取几个节点通信

- 最终一致性：信息在一定时间内传播到整个集群

#### 故障转移

```
1. 某节点超过 cluster-node-timeout 无响应 → 标记 PFAIL（疑似下线）
2. 半数以上 master 确认 → 标记 FAIL（客观下线）
3. 从该 master 的 slave 中选择新 master
4. 更新配置 epoch，广播新主节点
```

---

## 11. 分布式锁

### 11.1 基础实现

```bash
# 加锁（SET key value NX EX timeout）
SET lock:order:1001 "unique-client-id" NX EX 30
# 释放锁（Lua 脚本原子操作：先判断再删除）
EVAL "
  if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
  else
    return 0
  end
" 1 lock:order:1001 "unique-client-id"
```

### 11.2 常见问题与解决

**问题 1：锁过期但任务未完成**

```python
# 方案：看门狗（Watchdog）自动续期
import threading
def lock_with_watchdog(lock_key, client_id, ttl=30):
    r.set(lock_key, client_id, nx=True, ex=ttl)
    # 启动守护线程，每 ttl/3 秒续期
```

**问题 2：误释放其他客户端的锁**

```
加锁时 value 设为客户端唯一 ID
释放时：先 GET 校验 value == 自己的 ID，再 DEL
必须用 Lua 脚本保证原子性！
```

**问题 3：主从切换导致锁丢失**

```
Master 获得锁 → 数据未同步到 Slave → Master 挂了 → Slave 升级
                                                      ↑ 没有锁！
方案：Redlock（多个独立 Redis 节点，大多数加锁成功才算成功）
```

### 11.3 Redlock 算法

```
流程：
1. 获取当前时间戳 T1
2. 依次向 N 个独立 Redis 节点申请锁（相同的 key、value、短超时时间）
3. 计算总获取时间 = T2 - T1
4. 当获得锁的节点数 >= N/2 + 1，且总获取时间 < 锁有效期 → 加锁成功
5. 锁有效时间 = 原有效时间 - 总获取时间
6. 若获取失败，向所有节点发送释放命令
```

```python
# 使用 redlock-py
from redlock import Redlock
dlm = Redlock([{"host": "host1"}, {"host": "host2"}, {"host": "host3"}])
lock = dlm.lock("resource_key", 1000)  # 1000ms 有效期
# ... 业务逻辑 ...
dlm.unlock(lock)
```

### 11.4 乐观锁（WATCH + MULTI）

```bash
# 适合低冲突场景（如库存扣减）
WATCH stock:1001
stock = GET stock:1001          # stock = 10
if stock > 0:
    MULTI
    DECR stock:1001
    EXEC   # 如果 WATCH 后 stock 被修改，EXEC 返回 nil
```

---

## 12. 缓存三大问题与解决方案

### 12.1 缓存雪崩

**现象**：大量 key 在同一时间过期，所有请求打到数据库，数据库崩溃。

```
请求 → Redis（大量miss）→ MySQL（被打崩）
                          ↑
数据库重启 → 新请求涌入 → 又崩
```

**解决方案**：

```bash
# 1. 过期时间加随机值
SETEX user:1001:info $((3600 + RANDOM % 300)) "value"
# 2. 服务熔断 + 限流（如 Hystrix / Sentinel）
# 3. Redis 高可用（主从 + 哨兵 / Cluster）
# 4. 本地缓存（如 Ehcache）兜底
```

**时间维度的事前-事中-事后**：

| 阶段 | 措施 |
| --- | --- |
| **事前** | Redis 高可用、主从+哨兵，避免全盘崩溃 |
| **事中** | 本地缓存 + 限流降级（Hystrix/Sentinel），避免 DB 被打死 |
| **事后** | RDB + AOF 持久化，快速恢复缓存 |

### 12.2 缓存穿透

**现象**：查询缓存和数据库中都不存在的数据（如 id=-1），每一击都穿透缓存查 DB。

```
恶意请求 id=-1 → Redis（无）→ MySQL（无）→ 返回空
                   ↑_______________↓
                每次都重复这个过程 → DB 打崩
```

**解决方案**：

```bash
# 1. 参数校验：过滤不合理的请求（id < 0 直接拒绝）
# 2. 缓存空值：对不存在的数据也缓存（设置较短过期时间）
SET user:-1 "" EX 60
# 3. 布隆过滤器（推荐）
# 原理：高效判断 key 是否可能存在
#   - 返回"不存在" → 一定不存在，直接拒绝
#   - 返回"可能存在" → 继续查缓存和 DB
# 使用 RedisBloom 模块
BF.ADD user_filter 1001
BF.EXISTS user_filter 1001    # → 1（可能存在）
BF.EXISTS user_filter -1      # → 0（一定不存在）
```

**布隆过滤器原理**：

```
1. 初始化：长度为 m 的比特数组 + k 个哈希函数
2. 添加元素：用 k 个哈希函数计算 k 个位置，都置为 1
3. 查询元素：检查 k 个位置是否都为 1
   - 有一个为 0 → 一定不存在
   - 全为 1 → 可能存在（可能哈希冲突误判）
特点：
  - 空间效率高（1 亿 URL 约需 140MB）
  - 可以误判（假阳性），不会漏判（假阴性）
  - 不支持删除
```

### 12.3 缓存击穿

**现象**：某个热点 key 过期时，大量并发请求同时穿透缓存。

```
      热点 key 过期
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
  请求1  请求2  请求3  ...  同时查 DB！
    │      │      │
    ▼      ▼      ▼
  MySQL 遭受大量并发请求 → 崩溃
```

**解决方案**：

```python
# 1. 互斥锁：只让一个请求查 DB 更新缓存
import redis
def get_data(key):
    data = r.get(key)
    if data:
        return data
    # 尝试获取重建锁
    lock_key = f"lock:{key}"
    if r.set(lock_key, "1", nx=True, ex=10):
        data = query_db(key)
        r.setex(key, 3600, data)
        r.delete(lock_key)
        return data
    else:
        # 其他请求等待缓存重建
        time.sleep(0.1)
        return r.get(key)
```

```
请求流程：
  请求1 → key 过期 → 获取锁成功 → 查 DB → 更新缓存 → 释放锁
  请求2 → key 过期 → 获取锁失败 → 等待 → 缓存更新后读到
  请求3 → key 过期 → 获取锁失败 → 等待 → 缓存更新后读到
```

```bash
# 2. 热点数据永不过期
SET hot:data "value"         # 不设过期时间
# 异步更新：后台定时刷新热点数据
# 或通过逻辑过期时间 + 异步线程更新
```

### 12.4 三问题对比

| 问题 | 现象 | 核心原因 | 核心方案 |
| --- | --- | --- | --- |
| 雪崩 | 大批 key 同时过期 | 过期时间集中 | 随机化 TTL + 熔断降级 |
| 穿透 | 查询不存在的数据 | 默认无缓存 | 布隆过滤器 + 空值缓存 |
| 击穿 | 单个热点 key 过期 | 高并发竞争 | 互斥锁 + 永不过期 |

---

## 13. 线程模型与高性能原理

### 13.1 为什么 Redis 这么快？

| 因素 | 说明 |
| --- | --- |
| **纯内存操作** | 数据存在内存，类似 HashMap O(1) 访问 |
| **数据结构设计** | 专门为 Redis 设计，高效紧凑 |
| **单线程模型** | 无上下文切换和锁竞争 |
| **IO 多路复用** | 单线程监听多个 Socket，非阻塞 IO |
| **C 语言实现** | 贴近操作系统底层 |

### 13.2 文件事件处理器（File Event Handler）

```
                     ┌──────────────────┐
     Socket 1 ──────→│                  │
     Socket 2 ──────→│  IO 多路复用程序  │
     Socket 3 ──────→│  (epoll/select)  │
         ...         │                  │
                     └────────┬─────────┘
                              │ 事件放入队列
                              ▼
                     ┌──────────────────┐
                     │   事件分派器      │
                     └────────┬─────────┘
                              │ 逐个取出分发
          ┌───────────────────┼──────────────────┐
          ▼                   ▼                   ▼
   ┌────────────┐    ┌────────────┐    ┌────────────┐
   │ 连接应答   │    │ 命令请求   │    │ 命令回复   │
   │ 处理器     │    │ 处理器     │    │ 处理器     │
   └────────────┘    └────────────┘    └────────────┘
```

**4 个组成部分**：

1. **多个 Socket**：客户端连接

2. **IO 多路复用程序**：epoll/select 监听事件

3. **文件事件分派器**：将事件放入队列，逐个分发

4. **事件处理器**：命令请求处理、命令回复处理、连接应答处理

### 13.3 单线程 vs 多核利用

**单线程不浪费多核吗？**

| 方案 | 做法 |
| --- | --- |
| 单机多实例 | 一台机器起多个 Redis 进程，绑定不同 CPU 核心 |
| Redis Cluster | 集群分片，每个 master 都是一个独立进程 |
| Redis 6.0+ 多线程 IO | 网络读写多线程，命令执行仍单线程 |

> Redis 6.0 引入了 **多线程 IO**：只在线程读取请求和写回响应时使用多线程，**命令实际执行仍然是单线程的**，保证了原子性和线程安全。

```bash
# redis.conf - 开启多线程 IO
io-threads 4               # IO 线程数（建议不超过 CPU 核数）
io-threads-do-reads yes    # 开启读取多线程
```

### 13.4 Scan 代替 Keys

```bash
# ❌ KEYS 会阻塞 Redis
KEYS user:*
# ✅ SCAN 不会阻塞，可能返回重复
SCAN 0 MATCH user:* COUNT 1000
# 返回 (新游标, [key列表])
# 游标为 0 时迭代结束
# Hash 级别扫描
HSCAN user:hash 0 MATCH field:*
# Set 级别扫描
SSCAN user:set 0 MATCH member:*
# ZSet 级别扫描
ZSCAN user:zset 0 MATCH member:*
```

---

## 14. 常用命令速查

### String

| 命令 | 说明 |
| --- | --- |
| `SET key value [EX sec] [NX\|XX]` | 设置值，支持过期 |
| `GET key` | 获取值 |
| `DEL key` | 删除 |
| `INCR / DECR key` | 自增/自减 |
| `INCRBY / DECRBY key n` | 增减 n |
| `APPEND key value` | 追加 |
| `STRLEN key` | 获取长度 |
| `MSET / MGET` | 批量读写 |
| `GETSET key value` | 设新值返旧值 |
| `SETRANGE key offset value` | 覆盖指定位置 |

### Hash

| 命令 | 说明 |
| --- | --- |
| `HSET key field value` | 设置字段 |
| `HGET key field` | 获取字段 |
| `HMSET / HMGET` | 批量操作 |
| `HGETALL key` | 获取全部字段和值 |
| `HDEL key field` | 删除字段 |
| `HEXISTS key field` | 判断字段存在 |
| `HKEYS / HVALS` | 获取所有字段/值 |
| `HLEN key` | 字段数量 |
| `HINCRBY key field n` | 自增 |
| `HSCAN key cursor MATCH pattern` | 渐进扫描 |

### List

| 命令 | 说明 |
| --- | --- |
| `LPUSH / RPUSH key val` | 左/右插入 |
| `LPOP / RPOP key` | 左/右弹出 |
| `BLPOP / BRPOP key timeout` | 阻塞弹出 |
| `LLEN key` | 列表长度 |
| `LRANGE key start stop` | 范围查询（0 -1=全部） |
| `LTRIM key start stop` | 裁剪 |
| `LINDEX key index` | 按索引取值 |
| `LSET key index val` | 按索引设值 |
| `LINSERT key BEFORE\|AFTER pivot val` | 插入 |

### Set

| 命令 | 说明 |
| --- | --- |
| `SADD key member` | 添加 |
| `SREM key member` | 移除 |
| `SMEMBERS key` | 获取全部 |
| `SISMEMBER key member` | 判断存在 |
| `SCARD key` | 集合大小 |
| `SPOP key [count]` | 随机弹出 |
| `SRANDMEMBER key [count]` | 随机获取 |
| `SINTER / SUNION / SDIFF key1 key2` | 交/并/差集 |
| `SSCAN key cursor MATCH pattern` | 渐进扫描 |

### Sorted Set

| 命令 | 说明 |
| --- | --- |
| `ZADD key score member` | 添加 |
| `ZREM key member` | 移除 |
| `ZCARD key` | 大小 |
| `ZSCORE key member` | 获取分数 |
| `ZINCRBY key n member` | 增加分数 |
| `ZRANGE key start stop [WITHSCORES]` | 升序范围 |
| `ZREVRANGE key start stop [WITHSCORES]` | 降序范围 |
| `ZRANK / ZREVRANK key member` | 升/降序排名 |
| `ZRANGEBYSCORE key min max` | 按分数范围 |
| `ZREMRANGEBYRANK / ZREMRANGEBYSCORE` | 按排名/分数删除 |
| `ZCOUNT key min max` | 分数区间计数 |
| `ZUNIONSTORE / ZINTERSTORE` | 并/交集存储 |
| `ZPOPMIN / ZPOPMAX key [count]` | 弹出最小/大 |
| `ZSCAN key cursor MATCH pattern` | 渐进扫描 |

### 服务器管理

| 命令 | 说明 |
| --- | --- |
| `INFO [section]` | 服务器信息 |
| `CONFIG GET/SET param` | 查看/修改配置 |
| `CLIENT LIST` | 客户端列表 |
| `CLIENT KILL ip:port` | 断开客户端 |
| `SLOWLOG GET [n]` | 慢查询日志 |
| `DEBUG OBJECT key` | 调试信息 |
| `OBJECT ENCODING key` | 查看底层编码 |
| `MEMORY USAGE key` | 内存占用 |
| `DBSIZE` | 当前 DB 的 key 数量 |
| `FLUSHDB / FLUSHALL` | 清空当前 DB / 全部 |
| `MONITOR` | 实时监控命令 |
| `ROLE` | 复制角色 |
| `LATENCY DOCTOR` | 延迟诊断 |
