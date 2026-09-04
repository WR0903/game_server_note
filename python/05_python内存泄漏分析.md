# python内存泄漏分析

一、查看python进程中，某个类对象个数

```plain&#x20;text
import objgraph as og
p = og.by_type("HometownCell")
len(p)
```

二、分析某类对象引用关系

```plain&#x20;text
p = og.by_type('PlayerEntity')[0]
>>> og.show_backrefs(p)
Graph written to /tmp/objgraph-nq938697.dot (27 nodes)
Graph viewer (xdot) and image renderer (dot) not found, not doing anything else
```

然后使用 https://dreampuf.github.io/GraphvizOnline/  在线工具可以直接查看引用关系，确定是否有循环引用

三、泄漏分析步骤

首先在进程启动前查看进程各个对象的数量

\>>> import objgraph as og

\>>> og.most\_common\_types()

\[('dict', 111832), ('list', 82038), ('function', 9546), ('module', 7344), ('ModuleSpec', 7333), ('SourceFileLoader', 7222), ('method', 6233), ('DynamicDict', 5895), ('weakref', 5296), ('tuple', 5214)]

然后运行一段时间后把进程空闲后再看看内存各个对象数量，明显增加的是有泄漏

然后查看对应的引用关系分析为啥泄漏
