---
title: stl总结
category: C++
created_at: 2026-07-01 12:04:40
view_count: 16
---

# C++ STL 全面用法总结

> 涵盖容器、迭代器、算法、函数对象、工具类等核心组件，附可编译示例代码。

---

## 目录

1. [容器概览](#1-容器概览)
2. [序列容器](#2-序列容器)
3. [关联容器](#3-关联容器)
4. [无序容器](#4-无序容器)
5. [容器适配器](#5-容器适配器)
6. [迭代器](#6-迭代器)
7. [算法库](#7-算法库)
8. [函数对象与 Lambda](#8-函数对象与-lambda)
9. [工具类](#9-工具类)
10. [字符串与字符串视图](#10-字符串与字符串视图)
11. [智能指针](#11-智能指针)
12. [数值与随机数](#12-数值与随机数)
13. [容器选择指南](#13-容器选择指南)
14. [性能对比表](#14-性能对比表)

---

## 1. 容器概览

STL 容器按数据组织方式分为四大类：

| 类别 | 容器 | 特点 |
|------|------|------|
| 序列容器 | `vector`, `deque`, `list`, `forward_list`, `array` | 元素按插入顺序排列 |
| 关联容器 | `set`, `map`, `multiset`, `multimap` | 元素按键排序（红黑树） |
| 无序容器 | `unordered_set`, `unordered_map`, `unordered_multiset`, `unordered_multimap` | 哈希表实现 |
| 适配器 | `stack`, `queue`, `priority_queue` | 封装底层容器，提供受限接口 |

---

## 2. 序列容器

### 2.1 `std::vector` — 动态数组

**特点：** 连续内存、随机访问 O(1)、尾部插入均摊 O(1)、中间插入 O(n)。

```cpp
#include <vector>
#include <iostream>
#include <algorithm>

int main() {
    // 构造方式
    std::vector<int> v1;                     // 空
    std::vector<int> v2(5, 0);               // 5个0
    std::vector<int> v3 = {1, 2, 3, 4, 5};  // 初始化列表
    std::vector<int> v4(v3.begin(), v3.end()); // 迭代器范围

    // 容量操作
    v1.reserve(100);           // 预分配，避免频繁扩容
    std::cout << v1.capacity() << "\n";  // >= 100
    v1.shrink_to_fit();        // 释放多余内存

    // 元素访问
    v3[0];            // 不做边界检查
    v3.at(0);         // 越界抛 std::out_of_range
    v3.front();       // 第一个元素
    v3.back();        // 最后一个元素
    v3.data();        // 底层数组指针

    // 修改操作
    v3.push_back(6);               // 尾部追加
    v3.emplace_back(7);            // 原地构造，避免拷贝
    v3.insert(v3.begin() + 2, 99); // 在位置2插入
    v3.erase(v3.begin());          // 删除第一个
    v3.pop_back();                 // 删除最后一个

    // 遍历
    for (const auto& val : v3) {
        std::cout << val << " ";
    }

    // 常见技巧：erase-remove idiom（删除所有等于3的元素）
    v3.erase(std::remove(v3.begin(), v3.end(), 3), v3.end());

    // C++20: std::erase(v3, 3); 更简洁
}
```

**注意事项：**
- `push_back` 可能触发扩容（通常 2x），导致所有迭代器/指针失效
- 存储 `bool` 时 `vector<bool>` 是特化版本（位压缩），行为异常，建议用 `vector<char>` 或 `bitset`
- 大量中间插入/删除考虑用 `list` 或 `deque`

---

### 2.2 `std::deque` — 双端队列

**特点：** 分段连续内存、两端插入/删除 O(1)、随机访问 O(1)、中间插入 O(n)。

```cpp
#include <deque>

int main() {
    std::deque<int> dq = {2, 3, 4};

    dq.push_front(1);   // 头部插入
    dq.push_back(5);    // 尾部插入
    dq.pop_front();     // 头部删除
    dq.pop_back();      // 尾部删除

    // 随机访问
    dq[1];
    dq.at(1);

    // 与 vector 的区别：
    // 1. 两端操作都是 O(1)
    // 2. 不保证完全连续内存（分段存储）
    // 3. 没有 capacity() / reserve()
    // 4. 头部插入不会使已有迭代器失效（但中间插入会）
}
```

---

### 2.3 `std::list` — 双向链表

**特点：** 任意位置插入/删除 O(1)（已有迭代器时）、不支持随机访问、每个节点独立分配内存。

```cpp
#include <list>
#include <iostream>

int main() {
    std::list<int> lst = {3, 1, 4, 1, 5, 9};

    // 头尾操作
    lst.push_front(0);
    lst.push_back(10);

    // 在迭代器位置插入/删除
    auto it = std::next(lst.begin(), 3);
    lst.insert(it, 99);   // 在第3个位置前插入99
    lst.erase(it);        // 删除 it 指向的元素

    // list 专有算法（比通用算法更高效）
    lst.sort();                   // O(n log n) 归并排序
    lst.unique();                 // 删除连续重复元素（需先排序）
    lst.reverse();                // 反转

    // splice：O(1) 将另一个 list 的元素移过来
    std::list<int> other = {100, 200};
    lst.splice(lst.end(), other); // other 变空，元素转移到 lst

    // remove / remove_if
    lst.remove(1);                          // 删除所有值为1的
    lst.remove_if([](int x) { return x > 50; }); // 条件删除
}
```

---

### 2.4 `std::forward_list` — 单向链表

**特点：** 比 `list` 更省内存（无 prev 指针）、只能单向遍历、无 `size()` 方法。

```cpp
#include <forward_list>

int main() {
    std::forward_list<int> fl = {1, 2, 3, 4, 5};

    fl.push_front(0);          // 只能头部插入
    fl.pop_front();

    // 在某元素之后插入（因为单链表无法回溯）
    auto it = fl.begin();
    fl.insert_after(it, 99);   // 在第一个元素后插入99
    fl.erase_after(it);        // 删除 it 之后的元素

    fl.sort();
    fl.reverse();
}
```

---

### 2.5 `std::array` — 固定大小数组

**特点：** 编译期确定大小、栈上分配、零开销抽象（等同 C 数组但更安全）。

```cpp
#include <array>
#include <algorithm>

int main() {
    std::array<int, 5> arr = {5, 3, 1, 4, 2};

    arr.size();           // 编译期常量 5
    arr.fill(0);          // 全部置0
    arr[2];               // 随机访问
    arr.at(2);            // 带边界检查

    std::sort(arr.begin(), arr.end());

    // 可以作为函数参数传递（不退化为指针）
    // constexpr 上下文中可用
    constexpr std::array<int, 3> ca = {1, 2, 3};
    static_assert(ca[0] == 1);
}
```

---

## 3. 关联容器

底层实现为**红黑树**，元素自动按键排序，查找/插入/删除均为 O(log n)。

### 3.1 `std::set` / `std::multiset`

```cpp
#include <set>
#include <iostream>

int main() {
    // set：元素唯一
    std::set<int> s = {3, 1, 4, 1, 5}; // 实际存储 {1, 3, 4, 5}

    s.insert(2);          // 插入
    s.emplace(6);         // 原地构造
    s.erase(3);           // 按值删除
    s.count(4);           // 0 或 1
    s.contains(4);        // C++20: true/false

    // 查找
    auto it = s.find(4);
    if (it != s.end()) {
        std::cout << *it << "\n";
    }

    // 范围查找
    auto lo = s.lower_bound(2);  // >= 2 的第一个
    auto hi = s.upper_bound(4);  // > 4 的第一个
    // [lo, hi) 即 [2, 4] 区间的元素

    // multiset：允许重复
    std::multiset<int> ms = {1, 1, 2, 2, 3};
    ms.count(1);   // 2
    ms.erase(ms.find(1)); // 只删除一个1（而非全部）
}
```

### 3.2 `std::map` / `std::multimap`

```cpp
#include <map>
#include <string>
#include <iostream>

int main() {
    // 构造
    std::map<std::string, int> scores = {
        {"Alice", 95},
        {"Bob", 87},
        {"Charlie", 92}
    };

    // 插入
    scores["David"] = 88;                // operator[] 不存在则创建
    scores.insert({"Eve", 91});          // insert 不覆盖已有键
    scores.emplace("Frank", 85);
    scores.insert_or_assign("Alice", 96); // C++17: 存在则覆盖

    // 访问
    scores["Alice"];       // 不存在会插入默认值！慎用
    scores.at("Alice");    // 不存在抛异常

    // 查找
    if (auto it = scores.find("Bob"); it != scores.end()) {
        std::cout << it->first << ": " << it->second << "\n";
    }

    // 遍历（按键排序）
    for (const auto& [name, score] : scores) {  // C++17 结构化绑定
        std::cout << name << " -> " << score << "\n";
    }

    // 删除
    scores.erase("Charlie");
    scores.erase(scores.begin());

    // C++17: extract + insert 实现 O(1) 节点转移
    auto node = scores.extract("David");
    node.key() = "Dave";  // 修改键！
    scores.insert(std::move(node));

    // multimap：一个键对应多个值
    std::multimap<std::string, int> mm;
    mm.insert({"key", 1});
    mm.insert({"key", 2});
    auto range = mm.equal_range("key");
    for (auto it = range.first; it != range.second; ++it) {
        std::cout << it->second << "\n"; // 1, 2
    }
}
```

**自定义排序：**

```cpp
// 方法1：自定义比较器
struct CaseInsensitiveLess {
    bool operator()(const std::string& a, const std::string& b) const {
        return std::lexicographical_compare(
            a.begin(), a.end(), b.begin(), b.end(),
            [](char ca, char cb) { return tolower(ca) < tolower(cb); }
        );
    }
};
std::map<std::string, int, CaseInsensitiveLess> ci_map;

// 方法2：lambda（C++20 更方便）
auto cmp = [](int a, int b) { return a > b; }; // 降序
std::set<int, decltype(cmp)> desc_set(cmp);
```

---

## 4. 无序容器

底层实现为**哈希表**，平均 O(1) 查找/插入/删除，最坏 O(n)。

### 4.1 `std::unordered_set` / `std::unordered_map`

```cpp
#include <unordered_set>
#include <unordered_map>
#include <string>
#include <iostream>

int main() {
    // unordered_set
    std::unordered_set<int> us = {5, 2, 8, 1, 9};
    us.insert(3);
    us.erase(2);
    us.count(5);         // 0 或 1
    us.contains(5);      // C++20

    // 桶信息
    std::cout << "桶数: " << us.bucket_count() << "\n";
    std::cout << "负载因子: " << us.load_factor() << "\n";
    us.reserve(100);     // 预分配桶数
    us.max_load_factor(0.5); // 设置最大负载因子

    // unordered_map
    std::unordered_map<std::string, int> um;
    um["hello"] = 1;
    um.emplace("world", 2);

    // try_emplace (C++17): 如果键已存在则什么都不做
    um.try_emplace("hello", 999); // "hello" 已存在，不覆盖

    // 遍历（顺序不确定！）
    for (const auto& [k, v] : um) {
        std::cout << k << ": " << v << "\n";
    }
}
```

**自定义类型作为键：**

```cpp
#include <unordered_set>
#include <functional>

struct Point {
    int x, y;
    bool operator==(const Point& other) const {
        return x == other.x && y == other.y;
    }
};

// 方法1：特化 std::hash
namespace std {
    template<>
    struct hash<Point> {
        size_t operator()(const Point& p) const {
            return hash<int>()(p.x) ^ (hash<int>()(p.y) << 16);
        }
    };
}

// 方法2：自定义 hash functor
struct PointHash {
    size_t operator()(const Point& p) const {
        return std::hash<int>()(p.x) ^ (std::hash<int>()(p.y) << 16);
    }
};

int main() {
    std::unordered_set<Point> ps1;                    // 用方法1
    std::unordered_set<Point, PointHash> ps2;         // 用方法2
}
```

---

## 5. 容器适配器

适配器封装底层容器，提供受限接口。

### 5.1 `std::stack` — 后进先出

```cpp
#include <stack>

int main() {
    std::stack<int> st;          // 默认用 deque
    // std::stack<int, std::vector<int>> st; // 也可以用 vector

    st.push(1);
    st.push(2);
    st.push(3);
    st.top();    // 3（不弹出）
    st.pop();    // 弹出3
    st.size();   // 2
    st.empty();  // false
}
```

### 5.2 `std::queue` — 先进先出

```cpp
#include <queue>

int main() {
    std::queue<int> q;

    q.push(1);
    q.push(2);
    q.push(3);
    q.front();   // 1
    q.back();    // 3
    q.pop();     // 弹出1
}
```

### 5.3 `std::priority_queue` — 优先级队列（大顶堆）

```cpp
#include <queue>
#include <vector>
#include <functional>

int main() {
    // 默认大顶堆
    std::priority_queue<int> maxHeap;
    maxHeap.push(3);
    maxHeap.push(1);
    maxHeap.push(4);
    maxHeap.top();  // 4

    // 小顶堆
    std::priority_queue<int, std::vector<int>, std::greater<int>> minHeap;
    minHeap.push(3);
    minHeap.push(1);
    minHeap.push(4);
    minHeap.top();  // 1

    // 自定义比较
    auto cmp = [](const std::pair<int,int>& a, const std::pair<int,int>& b) {
        return a.second > b.second; // 按 second 升序
    };
    std::priority_queue<std::pair<int,int>, std::vector<std::pair<int,int>>,
                        decltype(cmp)> pq(cmp);
}
```

---

## 6. 迭代器

### 6.1 迭代器类别

| 类别 | 能力 | 典型容器 |
|------|------|----------|
| 输入迭代器 | 单遍读取 | `istream_iterator` |
| 输出迭代器 | 单遍写入 | `ostream_iterator`, `back_inserter` |
| 前向迭代器 | 多遍读写、`++` | `forward_list`, `unordered_*` |
| 双向迭代器 | `++`, `--` | `list`, `set`, `map` |
| 随机访问迭代器 | `+n`, `-n`, `[]` | `vector`, `deque`, `array` |
| 连续迭代器 (C++17) | 连续内存保证 | `vector`, `array`, `string` |

### 6.2 迭代器工具

```cpp
#include <iterator>
#include <vector>
#include <list>
#include <iostream>

int main() {
    std::vector<int> v = {10, 20, 30, 40, 50};

    // std::advance — 移动迭代器
    auto it = v.begin();
    std::advance(it, 3);   // it 现在指向 40

    // std::next / std::prev — 返回新迭代器（不修改原始）
    auto it2 = std::next(v.begin(), 2);  // 指向 30
    auto it3 = std::prev(v.end(), 1);    // 指向 50

    // std::distance — 计算两个迭代器之间的距离
    std::cout << std::distance(v.begin(), it2) << "\n"; // 2

    // 插入迭代器
    std::vector<int> dest;
    std::copy(v.begin(), v.end(), std::back_inserter(dest));  // 尾部插入

    std::list<int> lst;
    std::copy(v.begin(), v.end(), std::front_inserter(lst));  // 头部插入

    // 流迭代器
    std::copy(v.begin(), v.end(),
              std::ostream_iterator<int>(std::cout, ", ")); // 输出: 10, 20, 30, 40, 50,

    // 反向迭代器
    for (auto rit = v.rbegin(); rit != v.rend(); ++rit) {
        std::cout << *rit << " "; // 50 40 30 20 10
    }
}
```

---

## 7. 算法库

`<algorithm>` 是 STL 最强大的部分，提供 100+ 通用算法。

### 7.1 非修改算法

```cpp
#include <algorithm>
#include <vector>
#include <numeric>  // accumulate, iota
#include <iostream>

int main() {
    std::vector<int> v = {1, 2, 3, 4, 5, 3, 2, 1};

    // 查找
    auto it = std::find(v.begin(), v.end(), 3);         // 第一个3
    auto it2 = std::find_if(v.begin(), v.end(),
                            [](int x) { return x > 3; }); // 第一个>3的

    // 计数
    int cnt = std::count(v.begin(), v.end(), 3);        // 2
    int cnt2 = std::count_if(v.begin(), v.end(),
                             [](int x) { return x % 2 == 0; }); // 偶数个数

    // 判断
    bool allPos = std::all_of(v.begin(), v.end(), [](int x) { return x > 0; });
    bool anyBig = std::any_of(v.begin(), v.end(), [](int x) { return x > 4; });
    bool noneNeg = std::none_of(v.begin(), v.end(), [](int x) { return x < 0; });

    // 遍历（带副作用）
    std::for_each(v.begin(), v.end(), [](int x) { std::cout << x << " "; });

    // 最小/最大
    auto [minIt, maxIt] = std::minmax_element(v.begin(), v.end());
    std::cout << "min=" << *minIt << " max=" << *maxIt << "\n";

    // 比较两个范围
    std::vector<int> v2 = {1, 2, 3, 4, 5, 3, 2, 1};
    bool eq = std::equal(v.begin(), v.end(), v2.begin());

    // 搜索子序列
    std::vector<int> pattern = {3, 4, 5};
    auto found = std::search(v.begin(), v.end(), pattern.begin(), pattern.end());

    // 累加
    int sum = std::accumulate(v.begin(), v.end(), 0);
    int product = std::accumulate(v.begin(), v.end(), 1, std::multiplies<>());
}
```

### 7.2 修改算法

```cpp
#include <algorithm>
#include <vector>
#include <numeric>
#include <iostream>

int main() {
    std::vector<int> v = {5, 3, 1, 4, 2};

    // 填充
    std::vector<int> filled(10);
    std::fill(filled.begin(), filled.end(), 42);        // 全部42
    std::iota(filled.begin(), filled.end(), 1);         // 1,2,3,...,10
    std::generate(filled.begin(), filled.end(),
                  [n=0]() mutable { return n++ * n; }); // 自定义生成

    // 复制
    std::vector<int> dest(v.size());
    std::copy(v.begin(), v.end(), dest.begin());
    std::copy_if(v.begin(), v.end(), std::back_inserter(dest),
                 [](int x) { return x > 2; });  // 条件复制

    // 变换
    std::vector<int> doubled(v.size());
    std::transform(v.begin(), v.end(), doubled.begin(),
                   [](int x) { return x * 2; });

    // 两个范围的 transform
    std::vector<int> a = {1, 2, 3}, b = {4, 5, 6}, c(3);
    std::transform(a.begin(), a.end(), b.begin(), c.begin(),
                   [](int x, int y) { return x + y; }); // c = {5, 7, 9}

    // 替换
    std::replace(v.begin(), v.end(), 3, 99);            // 3 -> 99
    std::replace_if(v.begin(), v.end(),
                    [](int x) { return x < 3; }, 0);    // <3 的全换成 0

    // 移除（逻辑移除，需配合 erase）
    v = {1, 2, 3, 2, 4, 2, 5};
    auto newEnd = std::remove(v.begin(), v.end(), 2);
    v.erase(newEnd, v.end()); // v = {1, 3, 4, 5}

    // 去重（需先排序）
    v = {1, 1, 2, 2, 3, 3};
    auto last = std::unique(v.begin(), v.end());
    v.erase(last, v.end()); // v = {1, 2, 3}

    // 反转 & 旋转
    std::reverse(v.begin(), v.end());                   // 反转
    std::rotate(v.begin(), v.begin() + 1, v.end());     // 左旋1位

    // 随机打乱
    #include <random>
    std::mt19937 rng(42);
    std::shuffle(v.begin(), v.end(), rng);
}
```

### 7.3 排序与二分查找

```cpp
#include <algorithm>
#include <vector>
#include <iostream>

int main() {
    std::vector<int> v = {5, 2, 8, 1, 9, 3, 7, 4, 6};

    // 完全排序
    std::sort(v.begin(), v.end());                    // 升序
    std::sort(v.begin(), v.end(), std::greater<>());  // 降序

    // 稳定排序（保持等价元素相对顺序）
    std::stable_sort(v.begin(), v.end());

    // 部分排序：前k个最小
    std::partial_sort(v.begin(), v.begin() + 3, v.end());
    // 前3个位置是最小的3个元素（已排序），其余无序

    // nth_element：第n小的元素放到正确位置
    std::nth_element(v.begin(), v.begin() + 4, v.end());
    // v[4] 是第5小的元素，左边都<=它，右边都>=它

    // 二分查找（需已排序）
    std::sort(v.begin(), v.end());

    bool found = std::binary_search(v.begin(), v.end(), 5);

    auto lo = std::lower_bound(v.begin(), v.end(), 5);  // >= 5 的第一个
    auto hi = std::upper_bound(v.begin(), v.end(), 5);  // > 5 的第一个
    // [lo, hi) 是所有等于5的元素范围

    auto [first, last] = std::equal_range(v.begin(), v.end(), 5);
    // 等价于同时调用 lower_bound 和 upper_bound

    // 判断是否已排序
    bool sorted = std::is_sorted(v.begin(), v.end());

    // 合并两个已排序范围
    std::vector<int> a = {1, 3, 5}, b = {2, 4, 6}, merged;
    std::merge(a.begin(), a.end(), b.begin(), b.end(),
               std::back_inserter(merged)); // {1,2,3,4,5,6}

    // 原地合并（inplace_merge）
    std::vector<int> half_sorted = {1, 3, 5, 2, 4, 6};
    std::inplace_merge(half_sorted.begin(), half_sorted.begin() + 3,
                       half_sorted.end());
}
```

### 7.4 集合操作（需已排序）

```cpp
#include <algorithm>
#include <vector>
#include <iterator>
#include <iostream>

int main() {
    std::vector<int> a = {1, 2, 3, 4, 5};
    std::vector<int> b = {3, 4, 5, 6, 7};
    std::vector<int> result;

    // 交集
    std::set_intersection(a.begin(), a.end(), b.begin(), b.end(),
                          std::back_inserter(result));
    // result = {3, 4, 5}

    result.clear();
    // 并集
    std::set_union(a.begin(), a.end(), b.begin(), b.end(),
                   std::back_inserter(result));
    // result = {1, 2, 3, 4, 5, 6, 7}

    result.clear();
    // 差集 (a - b)
    std::set_difference(a.begin(), a.end(), b.begin(), b.end(),
                        std::back_inserter(result));
    // result = {1, 2}

    result.clear();
    // 对称差集
    std::set_symmetric_difference(a.begin(), a.end(), b.begin(), b.end(),
                                  std::back_inserter(result));
    // result = {1, 2, 6, 7}

    // 子集判断
    bool isSubset = std::includes(a.begin(), a.end(), result.begin(), result.end());
}
```

### 7.5 堆操作

```cpp
#include <algorithm>
#include <vector>
#include <iostream>

int main() {
    std::vector<int> v = {3, 1, 4, 1, 5, 9, 2, 6};

    // 建堆（大顶堆）
    std::make_heap(v.begin(), v.end());
    // v[0] 是最大值

    // 入堆
    v.push_back(10);
    std::push_heap(v.begin(), v.end()); // 新元素需在末尾

    // 出堆
    std::pop_heap(v.begin(), v.end()); // 最大值移到末尾
    int maxVal = v.back();
    v.pop_back();

    // 堆排序
    std::sort_heap(v.begin(), v.end()); // 需要先是有效堆

    // 判断是否为堆
    bool isHeap = std::is_heap(v.begin(), v.end());
}
```

### 7.6 排列组合

```cpp
#include <algorithm>
#include <vector>
#include <iostream>

int main() {
    std::vector<int> v = {1, 2, 3};

    // 生成所有排列
    std::sort(v.begin(), v.end()); // 必须先排序
    do {
        for (int x : v) std::cout << x << " ";
        std::cout << "\n";
    } while (std::next_permutation(v.begin(), v.end()));
    // 输出: 1 2 3, 1 3 2, 2 1 3, 2 3 1, 3 1 2, 3 2 1

    // prev_permutation：反向遍历
}
```

### 7.7 C++17/20 新增算法

```cpp
#include <algorithm>
#include <numeric>
#include <vector>
#include <string>

int main() {
    std::vector<int> v = {1, 2, 3, 4, 5};

    // C++17: clamp — 限制值在范围内
    int clamped = std::clamp(10, 1, 5); // 5

    // C++17: sample — 随机采样
    std::vector<int> sampled(3);
    std::mt19937 rng(42);
    std::sample(v.begin(), v.end(), sampled.begin(), 3, rng);

    // C++17: exclusive_scan / inclusive_scan（前缀和）
    std::vector<int> prefix(v.size());
    std::exclusive_scan(v.begin(), v.end(), prefix.begin(), 0);
    // prefix = {0, 1, 3, 6, 10}
    std::inclusive_scan(v.begin(), v.end(), prefix.begin());
    // prefix = {1, 3, 6, 10, 15}

    // C++17: reduce（可并行的 accumulate）
    int sum = std::reduce(v.begin(), v.end(), 0);

    // C++17: transform_reduce（map-reduce）
    std::vector<int> a = {1, 2, 3}, b = {4, 5, 6};
    int dot = std::transform_reduce(a.begin(), a.end(), b.begin(), 0);
    // 内积: 1*4 + 2*5 + 3*6 = 32

    // C++20: ranges 命名空间（见下文）
    // std::ranges::sort(v);
    // std::ranges::find(v, 3);
}
```

---

## 8. 函数对象与 Lambda

### 8.1 标准函数对象

```cpp
#include <functional>
#include <algorithm>
#include <vector>

int main() {
    std::vector<int> v = {5, 2, 8, 1, 9};

    // 算术
    std::plus<int>();         // a + b
    std::minus<int>();        // a - b
    std::multiplies<int>();   // a * b
    std::divides<int>();      // a / b
    std::modulus<int>();      // a % b
    std::negate<int>();       // -a

    // 比较
    std::equal_to<int>();     // a == b
    std::not_equal_to<int>(); // a != b
    std::greater<int>();      // a > b
    std::less<int>();         // a < b
    std::greater_equal<int>();// a >= b
    std::less_equal<int>();   // a <= b

    // 逻辑
    std::logical_and<int>();  // a && b
    std::logical_or<int>();   // a || b
    std::logical_not<int>();  // !a

    // 透明比较器 (C++14): 省略模板参数
    std::sort(v.begin(), v.end(), std::greater<>()); // 降序

    // 用 multiplies 做累积
    #include <numeric>
    int product = std::accumulate(v.begin(), v.end(), 1, std::multiplies<>());
}
```

### 8.2 Lambda 表达式

```cpp
#include <functional>
#include <vector>
#include <algorithm>
#include <iostream>

int main() {
    // 基本语法: [捕获列表](参数) -> 返回类型 { 函数体 }
    auto add = [](int a, int b) { return a + b; };

    // 捕获方式
    int x = 10, y = 20;
    auto byVal = [x, y]() { return x + y; };          // 值捕获（只读）
    auto byRef = [&x, &y]() { x++; y++; };            // 引用捕获
    auto allVal = [=]() { return x + y; };             // 全部值捕获
    auto allRef = [&]() { x++; y++; };                 // 全部引用捕获
    auto mixed = [&x, y]() { x += y; };               // 混合

    // mutable：允许修改值捕获的副本
    auto counter = [n = 0]() mutable { return ++n; };
    std::cout << counter() << counter() << counter(); // 1 2 3

    // 初始化捕获 (C++14): move 语义
    auto ptr = std::make_unique<int>(42);
    auto lambda = [p = std::move(ptr)]() { return *p; };

    // 泛型 lambda (C++14)
    auto generic = [](auto a, auto b) { return a + b; };
    generic(1, 2);       // int
    generic(1.0, 2.0);   // double
    generic(std::string("a"), std::string("b")); // string

    // 模板 lambda (C++20)
    auto tmpl = []<typename T>(std::vector<T>& v) { return v.size(); };

    // 立即调用 (IIFE)
    const auto result = [&]() {
        // 复杂初始化逻辑
        return x * y;
    }();

    // 递归 lambda（需 std::function 或 Y-combinator）
    std::function<int(int)> fib = [&fib](int n) -> int {
        return n <= 1 ? n : fib(n - 1) + fib(n - 2);
    };
}
```

### 8.3 `std::function` — 通用可调用包装

```cpp
#include <functional>
#include <iostream>

void freeFunc(int x) { std::cout << "free: " << x << "\n"; }

struct Functor {
    void operator()(int x) const { std::cout << "functor: " << x << "\n"; }
};

struct Obj {
    int val = 42;
    void method(int x) { std::cout << "method: " << val + x << "\n"; }
};

int main() {
    // 包装各种可调用对象
    std::function<void(int)> f;

    f = freeFunc;                     // 普通函数
    f(1);

    f = Functor{};                    // 函数对象
    f(2);

    f = [](int x) { std::cout << "lambda: " << x << "\n"; };
    f(3);                             // lambda

    // 成员函数
    std::function<void(Obj&, int)> mf = &Obj::method;
    Obj obj;
    mf(obj, 10);

    // std::bind
    auto bound = std::bind(&Obj::method, &obj, std::placeholders::_1);
    bound(20);

    // 注意：std::function 有性能开销（类型擦除 + 可能堆分配）
    // 如果不需要存储，用 auto + lambda 或模板参数更高效
}
```

---

## 9. 工具类

### 9.1 `std::pair` 与 `std::tuple`

```cpp
#include <tuple>
#include <utility>
#include <string>
#include <iostream>

int main() {
    // pair
    std::pair<int, std::string> p = {1, "hello"};
    auto p2 = std::make_pair(2, "world");
    std::cout << p.first << " " << p.second << "\n";

    // tuple
    std::tuple<int, double, std::string> t = {1, 3.14, "pi"};
    auto t2 = std::make_tuple(2, 2.71, "e");

    // 访问
    std::get<0>(t);   // 1
    std::get<1>(t);   // 3.14
    std::get<2>(t);   // "pi"

    // 结构化绑定 (C++17)
    auto [i, d, s] = t;

    // tie：绑定到已有变量
    int a; double b; std::string c;
    std::tie(a, b, c) = t;
    std::tie(a, std::ignore, c) = t;  // 忽略某些值

    // tuple 比较（按字典序）
    auto t3 = std::make_tuple(1, 2);
    auto t4 = std::make_tuple(1, 3);
    bool less = t3 < t4; // true

    // tuple_cat：拼接
    auto combined = std::tuple_cat(t, t2);
    // combined 有 6 个元素

    // std::apply：展开 tuple 为函数参数
    auto sum = [](int x, double y, const std::string& z) {
        return x + y;
    };
    double result = std::apply(sum, t);
}
```

### 9.2 `std::optional` (C++17)

```cpp
#include <optional>
#include <string>
#include <iostream>

std::optional<int> findIndex(const std::vector<int>& v, int target) {
    for (size_t i = 0; i < v.size(); ++i) {
        if (v[i] == target) return static_cast<int>(i);
    }
    return std::nullopt; // 未找到
}

int main() {
    std::optional<int> opt;            // 空
    std::optional<int> opt2 = 42;      // 有值

    // 检查是否有值
    if (opt2.has_value()) { /* ... */ }
    if (opt2) { /* ... */ }

    // 取值
    int val = opt2.value();          // 空时抛 bad_optional_access
    int val2 = opt2.value_or(-1);    // 空时返回默认值
    int val3 = *opt2;                // 不检查，空时UB

    // 赋值 / 重置
    opt = 100;
    opt.reset();       // 变空
    opt.emplace(200);  // 原地构造

    // 实际用法
    std::vector<int> v = {1, 2, 3, 4, 5};
    if (auto idx = findIndex(v, 3)) {
        std::cout << "found at index " << *idx << "\n";
    }
}
```

### 9.3 `std::variant` (C++17)

```cpp
#include <variant>
#include <string>
#include <iostream>

int main() {
    // 类型安全的 union
    std::variant<int, double, std::string> v;

    v = 42;
    v = 3.14;
    v = "hello";

    // 取值
    std::string& s = std::get<std::string>(v);       // 类型不匹配抛异常
    std::string* p = std::get_if<std::string>(&v);   // 不匹配返回 nullptr

    // 判断当前类型
    v.index();                              // 当前是第几个类型 (0/1/2)
    std::holds_alternative<int>(v);         // false
    std::holds_alternative<std::string>(v); // true

    // 访问者模式（最常用）
    std::visit([](auto&& arg) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same_v<T, int>) {
            std::cout << "int: " << arg << "\n";
        } else if constexpr (std::is_same_v<T, double>) {
            std::cout << "double: " << arg << "\n";
        } else {
            std::cout << "string: " << arg << "\n";
        }
    }, v);

    // overloaded 辅助（惯用法）
    template<class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
    // C++20 不需要推导指引
    // 使用:
    // std::visit(overloaded{
    //     [](int i) { ... },
    //     [](double d) { ... },
    //     [](const std::string& s) { ... }
    // }, v);
}
```

### 9.4 `std::any` (C++17)

```cpp
#include <any>
#include <string>
#include <iostream>

int main() {
    std::any a;                // 空
    a = 42;                    // int
    a = std::string("hello");  // string

    // 取值
    std::string s = std::any_cast<std::string>(a);     // 类型不匹配抛异常
    auto* p = std::any_cast<std::string>(&a);          // 不匹配返回 nullptr

    // 检查
    a.has_value();      // true
    a.type().name();    // typeid 名称（实现定义）
    a.reset();          // 清空

    // 注意：any 通常用于需要完全类型擦除的场景
    // 如果类型集合已知，优先用 variant
}
```

---

## 10. 字符串与字符串视图

### 10.1 `std::string`

```cpp
#include <string>
#include <iostream>
#include <sstream>
#include <algorithm>

int main() {
    // 构造
    std::string s1 = "Hello";
    std::string s2(5, 'x');        // "xxxxx"
    std::string s3(s1, 1, 3);     // "ell" (从位置1取3个字符)

    // 拼接
    std::string s = s1 + " World";
    s += "!";
    s.append(" C++");

    // 查找
    size_t pos = s.find("World");        // 找到返回位置，未找到返回 npos
    size_t rpos = s.rfind("l");          // 从后往前找
    size_t fof = s.find_first_of("aeiou"); // 第一个元音

    if (pos != std::string::npos) {
        std::cout << "found at " << pos << "\n";
    }

    // 子串
    std::string sub = s.substr(0, 5);  // "Hello"

    // 替换
    s.replace(6, 5, "STL");            // 从位置6替换5个字符

    // 插入 / 删除
    s.insert(0, ">> ");
    s.erase(0, 3);

    // 比较
    s.compare("other");        // <0, 0, >0
    s.starts_with("Hello");    // C++20
    s.ends_with("C++");        // C++20
    s.contains("World");       // C++23

    // 数值转换
    int n = std::stoi("42");
    double d = std::stod("3.14");
    std::string ns = std::to_string(42);

    // 分割（STL 没有直接的 split，用 stringstream）
    std::istringstream iss("one two three");
    std::string word;
    while (iss >> word) {
        std::cout << word << "\n";
    }

    // 或用 getline 按分隔符
    std::istringstream csv("a,b,c,d");
    std::string token;
    while (std::getline(csv, token, ',')) {
        std::cout << token << "\n";
    }

    // 大小写转换
    std::string lower = s;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
}
```

### 10.2 `std::string_view` (C++17)

```cpp
#include <string_view>
#include <string>
#include <iostream>

// 零拷贝的字符串引用
void print(std::string_view sv) {
    std::cout << sv << " (len=" << sv.size() << ")\n";
}

int main() {
    std::string s = "Hello World";
    const char* cs = "C-string";

    // 可以从 string、char*、字面量构造，无拷贝
    print(s);
    print(cs);
    print("literal");

    // 子串操作也是零拷贝
    std::string_view sv = s;
    auto sub = sv.substr(0, 5);   // "Hello"，不分配内存
    sv.remove_prefix(6);          // "World"
    sv.remove_suffix(1);          // "Worl"

    // 查找、比较等接口与 string 相同
    sv.find("or");
    sv.starts_with("W");

    // 注意：string_view 不拥有数据！
    // 不要返回局部 string 的 string_view
    // 不要在 string 被销毁后使用其 string_view
}
```

---

## 11. 智能指针

```cpp
#include <memory>
#include <iostream>

struct Widget {
    int id;
    Widget(int i) : id(i) { std::cout << "Widget " << id << " created\n"; }
    ~Widget() { std::cout << "Widget " << id << " destroyed\n"; }
};

int main() {
    // unique_ptr：独占所有权
    auto up = std::make_unique<Widget>(1);
    // auto up2 = up;              // 编译错误！不可拷贝
    auto up2 = std::move(up);      // 可移动
    up2->id;                        // 使用
    up2.reset();                    // 手动释放

    // unique_ptr 数组
    auto arr = std::make_unique<int[]>(10);
    arr[0] = 42;

    // shared_ptr：共享所有权（引用计数）
    auto sp1 = std::make_shared<Widget>(2);
    auto sp2 = sp1;                 // 引用计数 +1
    std::cout << sp1.use_count() << "\n"; // 2
    sp2.reset();                    // 引用计数 -1

    // weak_ptr：不增加引用计数，用于打破循环引用
    std::weak_ptr<Widget> wp = sp1;
    if (auto locked = wp.lock()) {  // 尝试获取 shared_ptr
        std::cout << "alive: " << locked->id << "\n";
    }

    // 自定义删除器
    auto fileDeleter = [](FILE* f) { if (f) fclose(f); };
    std::unique_ptr<FILE, decltype(fileDeleter)> fp(fopen("test.txt", "r"), fileDeleter);

    // enable_shared_from_this：安全地从 this 获取 shared_ptr
    struct Node : std::enable_shared_from_this<Node> {
        std::shared_ptr<Node> getPtr() { return shared_from_this(); }
    };
}
```

---

## 12. 数值与随机数

### 12.1 `<numeric>` 数值算法

```cpp
#include <numeric>
#include <vector>
#include <iostream>

int main() {
    std::vector<int> v = {1, 2, 3, 4, 5};

    // 累积
    int sum = std::accumulate(v.begin(), v.end(), 0);           // 15
    int product = std::accumulate(v.begin(), v.end(), 1,
                                  std::multiplies<>());          // 120

    // 内积
    std::vector<int> w = {2, 3, 4, 5, 6};
    int dot = std::inner_product(v.begin(), v.end(), w.begin(), 0); // 70

    // 前缀和
    std::vector<int> prefix(v.size());
    std::partial_sum(v.begin(), v.end(), prefix.begin());
    // prefix = {1, 3, 6, 10, 15}

    // 相邻差分
    std::vector<int> diff(v.size());
    std::adjacent_difference(v.begin(), v.end(), diff.begin());
    // diff = {1, 1, 1, 1, 1}

    // iota：递增填充
    std::vector<int> seq(10);
    std::iota(seq.begin(), seq.end(), 1); // {1, 2, 3, ..., 10}

    // C++17: GCD / LCM
    int g = std::gcd(12, 8);   // 4
    int l = std::lcm(12, 8);   // 24

    // C++17: reduce（可并行）
    int rsum = std::reduce(v.begin(), v.end());

    // C++17: transform_reduce
    int sumSq = std::transform_reduce(v.begin(), v.end(), 0,
                                       std::plus<>(),
                                       [](int x) { return x * x; });
    // 1+4+9+16+25 = 55
}
```

### 12.2 `<random>` 随机数

```cpp
#include <random>
#include <iostream>
#include <algorithm>
#include <vector>

int main() {
    // 随机引擎
    std::random_device rd;           // 硬件随机数（种子源）
    std::mt19937 gen(rd());          // Mersenne Twister（最常用）
    std::mt19937_64 gen64(rd());     // 64位版本

    // 分布
    std::uniform_int_distribution<int> uni(1, 100);     // [1, 100] 均匀整数
    std::uniform_real_distribution<double> unif(0.0, 1.0); // [0, 1) 均匀浮点
    std::normal_distribution<double> normal(0.0, 1.0);  // 正态分布
    std::bernoulli_distribution bern(0.7);              // 70%概率返回true
    std::poisson_distribution<int> poisson(4.0);        // 泊松分布

    // 使用
    int randInt = uni(gen);
    double randFloat = unif(gen);
    double randNormal = normal(gen);
    bool coin = bern(gen);

    // 打乱容器
    std::vector<int> v = {1, 2, 3, 4, 5};
    std::shuffle(v.begin(), v.end(), gen);

    // 生成一组随机数
    std::vector<int> randoms(100);
    std::generate(randoms.begin(), randoms.end(),
                  [&]() { return uni(gen); });
}
```

---

## 13. 容器选择指南

### 按需求选择容器：

```
需要快速随机访问？
├── 是 → 大小固定？
│       ├── 是 → std::array
│       └── 否 → std::vector（首选）或 std::deque（需要头部插入）
└── 否 → 需要排序？
        ├── 是 → 需要重复键？
        │       ├── 是 → std::multiset / std::multimap
        │       └── 否 → std::set / std::map
        └── 否 → 需要 O(1) 查找？
                ├── 是 → std::unordered_set / std::unordered_map
                └── 否 → 频繁中间插入删除？
                        ├── 是 → std::list
                        └── 否 → std::vector（缓存友好）
```

### 快速决策表：

| 场景 | 推荐容器 |
|------|----------|
| 默认选择 | `vector` |
| 键值对查找 | `unordered_map` |
| 有序键值对 | `map` |
| 去重集合 | `unordered_set` |
| 有序集合 | `set` |
| FIFO 队列 | `queue` |
| LIFO 栈 | `stack` |
| 优先级调度 | `priority_queue` |
| 频繁两端操作 | `deque` |
| 频繁中间插入/链表拼接 | `list` |
| 内存极其紧张的链表 | `forward_list` |
| 固定大小的小数组 | `array` |

---

## 14. 性能对比表

### 时间复杂度

| 操作 | vector | deque | list | set/map | unordered_set/map |
|------|--------|-------|------|---------|-------------------|
| 随机访问 | O(1) | O(1) | O(n) | O(log n) | O(n) |
| 头部插入 | O(n) | O(1) | O(1) | - | - |
| 尾部插入 | O(1)* | O(1) | O(1) | - | - |
| 中间插入 | O(n) | O(n) | O(1)+ | O(log n) | O(1)* |
| 查找 | O(n) | O(n) | O(n) | O(log n) | O(1)* |
| 删除 | O(n) | O(n) | O(1)+ | O(log n) | O(1)* |

> \* 均摊复杂度 + 已有迭代器时

### 内存特征

| 容器 | 内存布局 | 额外开销/元素 |
|------|----------|---------------|
| `vector` | 连续 | ~0（可能有未用容量） |
| `deque` | 分段连续 | 指针数组 |
| `list` | 散布 | 2 指针 (prev/next) |
| `forward_list` | 散布 | 1 指针 (next) |
| `set/map` | 树节点散布 | 3 指针 + 颜色位 |
| `unordered_*` | 桶数组 + 链表 | 哈希值 + 指针 |

---

## 附录：C++20 Ranges 简介

C++20 引入 Ranges 库，让算法调用更简洁、可组合：

```cpp
#include <ranges>
#include <vector>
#include <algorithm>
#include <iostream>

int main() {
    std::vector<int> v = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 直接传容器（不用 begin/end）
    std::ranges::sort(v);
    auto it = std::ranges::find(v, 5);

    // 视图（惰性求值，零拷贝）
    auto even = v | std::views::filter([](int x) { return x % 2 == 0; });
    auto squared = v | std::views::transform([](int x) { return x * x; });

    // 管道组合
    auto result = v
        | std::views::filter([](int x) { return x % 2 == 0; })
        | std::views::transform([](int x) { return x * x; })
        | std::views::take(3);

    for (int x : result) {
        std::cout << x << " "; // 4 16 36
    }

    // 常用视图
    std::views::iota(1, 11);        // 生成 1~10
    std::views::reverse(v);         // 反转视图
    std::views::drop(v, 3);         // 跳过前3个
    std::views::take(v, 5);         // 取前5个

    // 投影 (Projection)
    struct Person { std::string name; int age; };
    std::vector<Person> people = {{"Alice", 30}, {"Bob", 25}, {"Charlie", 35}};
    std::ranges::sort(people, {}, &Person::age); // 按 age 排序
}
```

---

## 附录：常见陷阱与最佳实践

### 1. 迭代器失效

```cpp
// 错误：遍历中修改 vector
std::vector<int> v = {1, 2, 3, 4, 5};
for (auto it = v.begin(); it != v.end(); ++it) {
    if (*it == 3) v.erase(it); // it 失效！UB
}

// 正确：erase 返回下一个有效迭代器
for (auto it = v.begin(); it != v.end(); ) {
    if (*it == 3) it = v.erase(it);
    else ++it;
}

// 更好：erase-remove idiom
v.erase(std::remove(v.begin(), v.end(), 3), v.end());

// C++20 最佳
std::erase(v, 3);
```

### 2. `map` 的 `operator[]` 副作用

```cpp
std::map<std::string, int> m;
// 读取不存在的键会插入默认值
int val = m["missing"]; // m 现在有 {"missing": 0}

// 用 find 或 count 检查
if (auto it = m.find("key"); it != m.end()) {
    int val = it->second;
}
```

### 3. `reserve` vs `resize`

```cpp
std::vector<int> v;
v.reserve(100);  // 分配内存，size 仍为 0，不能用 v[i]
v.resize(100);   // 分配内存 + 创建 100 个元素（默认初始化）
```

### 4. 移动语义与容器

```cpp
std::vector<std::string> v;
std::string s = "hello";

v.push_back(s);             // 拷贝
v.push_back(std::move(s));  // 移动（s 变为有效但未指定状态）
v.emplace_back("world");    // 原地构造（最高效）
```

### 5. 范围 for 循环的引用

```cpp
std::vector<std::string> v = {"long string", "another"};

// 不必要的拷贝
for (auto s : v) { /* s 是拷贝 */ }

// 只读访问
for (const auto& s : v) { /* 无拷贝 */ }

// 需要修改
for (auto& s : v) { s += " modified"; }
```
