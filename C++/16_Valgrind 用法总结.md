## 1. Valgrind 工具套件概览



- **Memcheck** — 内存错误检测（最常用）

- **Callgrind** — 函数调用/性能剖析

- **Cachegrind** — 缓存命中率分析

- **Helgrind** — 多线程竞态条件检测

- **Massif** — 堆内存占用分析

- **DRD** — 多线程错误检测



---



## 2. Memcheck — 内存错误检测



### 2.1 基本用法



```bash

# 编译时加 -g 获取行号（推荐 -O0 防止优化干扰）

gcc -g -O0 your_program.c -o your_program



# 基本检测

valgrind --tool=memcheck ./your_program



# 完整检测（推荐组合）

valgrind --tool=memcheck \

  --leak-check=full \

  --track-origins=yes \

  --show-reachable=yes \

  --num-callers=20 \

  ./your_program arg1 arg2

```



### 2.2 关键选项



- `--leak-check=full` — 显示每个泄漏的详细信息

- `--track-origins=yes` — 跟踪未初始化值的来源

- `--show-reachable=yes` — 显示程序结束时仍可达的内存

- `--num-callers=N` — 显示 N 层调用栈

- `--suppressions=file` — 使用抑制文件忽略已知误报

- `--gen-suppressions=all` — 自动生成抑制规则



### 2.3 泄漏分类



- **Definitely lost** — 确定泄漏，无指针指向该内存

- **Indirectly lost** — 间接泄漏，指向该内存的指针本身也泄漏了

- **Possibly lost** — 可能泄漏，指针指向了分配块内部位置

- **Still reachable** — 程序结束时仍可达（全局变量等，通常无需修复）



### 2.4 检测的错误类型



- 非法读写 — 访问未分配或已释放的内存

- 使用未初始化值 — 使用未初始化的变量

- 内存泄漏 — malloc/new 后未 free/delete

- 双重释放 — 同一块内存释放两次

- 不匹配的分配/释放 — malloc+delete 或 new+free 混用



### 2.5 输出示例解读



```

==12345== Invalid read of size 4

==12345==    at 0x400567: main (test.c:10)

==12345==  Address 0x5203040 is 0 bytes inside a block of size 40 free'd

==12345==    at 0x4C30D3B: free (vg_replace_malloc.c:530)

==12345==    by 0x400550: main (test.c:9)

```



> `==PID==` 前缀标识进程，错误类型 + 位置 + 原因链一目了然。



---



## 3. Callgrind — 函数调用剖析



### 3.1 基本用法



```bash

# 运行剖析（输出 callgrind.out.<pid>）

valgrind --tool=callgrind ./your_program



# 只统计指令数（快速模式）

valgrind --tool=callgrind --cache=no ./your_program



# 统计缓存行为

valgrind --tool=callgrind --cache=yes ./your_program



# 只剖析特定函数

valgrind --tool=callgrind --collect-atstart=no --toggle-collect=function_name ./your_program



# 控制调用栈深度

valgrind --tool=callgrind --callgrind-out-file=callgrind.out ./your_program

```



### 3.2 结果分析方式



#### 方式一：KCachegrind GUI



```bash

kcachegrind callgrind.out.<pid>

```



#### 方式二：gprof2dot 生成调用图（重点，详见第 4 章）



---



## 4. Callgrind + gprof2dot 联合使用（堆栈可视化）



### 4.1 安装依赖



```bash

# Ubuntu/Debian

sudo apt install valgrind python3 graphviz



# 安装 gprof2dot

pip install gprof2dot



# 或直接下载脚本

wget https://raw.githubusercontent.com/jrfonseca/gprof2dot/master/gprof2dot.py

```



### 4.2 完整流程



```bash

# Step 1: 编译程序（加 -g）

gcc -g -O0 -o myapp myapp.c



# Step 2: 用 Callgrind 运行剖析

valgrind --tool=callgrind ./myapp



# Step 3: 生成输出文件 callgrind.out.<pid>



# Step 4: 用 gprof2dot 转换为 DOT 格式并生成图片

gprof2dot -f callgrind callgrind.out.<pid> | dot -Tpng -o callgraph.png



# 或生成 SVG（更适合浏览器查看）

gprof2dot -f callgrind callgrind.out.<pid> | dot -Tsvg -o callgraph.svg



# 或生成 PDF

gprof2dot -f callgrind callgrind.out.<pid> | dot -Tpdf -o callgraph.pdf

```



### 4.3 gprof2dot 选项详解



```bash

# 只显示耗时超过阈值的函数（过滤噪音）

gprof2dot -f callgrind callgrind.out.12345 \

  --threshold=5 \

  | dot -Tpng -o callgraph.png



# 阈值说明：

#   --threshold=0  显示所有函数（默认）

#   --threshold=5  只显示占总时间 ≥5% 的节点

#   --threshold=10 只显示占 ≥10% 的节点



# 指定输出 DOT 文件

gprof2dot -f callgrind callgrind.out.12345 -o callgraph.dot



# 自定义节点/边过滤阈值

gprof2dot -f callgrind callgrind.out.12345 \

  --node-threshold=2 \

  --edge-threshold=2 \

  | dot -Tpng -o callgraph.png



# 剥离路径前缀（简化显示）

gprof2dot -f callgrind callgrind.out.12345 \

  --strip \

  | dot -Tpng -o callgraph.png

```



### 4.4 输出图解读



生成的调用图中：



- **节点** = 函数，大小代表耗时占比，颜色从绿（快）到红（慢）

- **边** = 调用关系，粗细代表调用次数/耗时占比

- 每个节点标注：`函数名 (总时间, 自身时间, 调用次数)`

- 颜色梯度：绿色（0%）→ 黄色（中间）→ 红色（100% 热点）



### 4.5 一键脚本示例



```bash

#!/bin/bash

# profile.sh — 一键生成调用图



APP=${1:?"Usage: $0 <executable> [args...]"}

ARGS="${@:2}"



echo "[1] Running Callgrind on $APP..."

valgrind --tool=callgrind --cache=no "$APP" $ARGS



PID=$(ls -t callgrind.out.* | head -1)

echo "[2] Found profile: $PID"



echo "[3] Generating call graph..."

gprof2dot -f callgrind --threshold=2 "$PID" | dot -Tpng -o callgraph.png

gprof2dot -f callgrind --threshold=2 "$PID" | dot -Tsvg -o callgraph.svg



echo "[4] Done! Open callgraph.png or callgraph.svg"

```



---



## 5. gprof + gprof2dot（传统剖析方式）



gprof2dot 也支持 gprof 格式：



```bash

# 编译时加 -pg

gcc -pg -g -O0 -o myapp myapp.c



# 运行（生成 gmon.out）

./myapp



# 生成 gprof 报告

gprof myapp gmon.out > profile.txt



# 用 gprof2dot 转换

gprof2dot -f prof profile.txt | dot -Tpng -o callgraph.png

```



### gprof2dot 支持的输入格式



- `-f callgrind` — Valgrind Callgrind 输出

- `-f prof` — gprof 文本输出

- `-f dot` — DOT 格式

- `-f perf` — Linux perf 报告

- `-f oprofile` — OProfile 报告

- `-f hprof` — Java hprof

- `-f python` — cProfile/pstats



---



## 6. Callgrind 注释源码



```bash

# 在源码中逐行标注执行次数

callgrind_annotate callgrind.out.<pid> --auto=yes source.c

```



输出示例：



```

-- line 10:  500,000  for (i = 0; i < N; i++)

-- line 11:  500,000      sum += arr[i];

```



---



## 7. Cachegrind — 缓存分析



```bash

valgrind --tool=cachegrind ./your_program



# 逐行注释

cg_annotate cachegrind.out.<pid> --auto=yes source.c

```



---



## 8. Helgrind / DRD — 线程检测



```bash

# Helgrind（竞态条件检测）

valgrind --tool=helgrind ./your_program



# DRD（更快的线程检测）

valgrind --tool=drd ./your_program

```



检测内容：数据竞态、锁顺序违反、死锁风险等。



---



## 9. Massif — 堆内存分析



```bash

valgrind --tool=massif ./your_program



# 查看结果

ms_print massif.out.<pid>

```



---



## 10. 局限性



- 仅支持 **Linux**（macOS/Windows 不支持）

- 运行速度降低 10~50x（Memcheck 约 20x，Callgrind 约 10~20x）

- 无法检测静态分配（栈/全局）的越界访问

- 需 `-g` 编译才能显示行号

- 对多线程程序需配合 Helgrind/DRD



---



## 11. 替代方案对比



- **Valgrind/Memcheck**（Linux，速度降低约 20x）— 全面内存检测

- **Callgrind**（Linux，速度降低约 10~20x）— 详细调用剖析

- **AddressSanitizer**（全平台，速度降低约 2x）— 编译器内置，速度快

- **perf + gprof2dot**（Linux，速度降低约 1x）— 系统级剖析，极快

- **gprof**（Linux，速度降低约 1x）— 传统剖析，需 -pg 编译选项

- **Dr. Memory**（Linux/Windows，速度降低约 10x）— Windows 可用的内存检测



