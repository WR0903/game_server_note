---
title: json.dumps遇到中文会乱码
category: python
created_at: 2026-04-26 12:31:09
view_count: 0
---

## json.dumps遇到中文会乱码

### 问题描述
```
import json
a = {'1': "您好"}
print(json.dumps(a))
```
输出结果为：  
```
{"1": "\u60a8\u597d"} 
```
出现乱码

### 解决方法

```
import json
a = {'1': "您好"}
print(json.dumps(a, ensure_ascii=False))
```

输出结果：

```
{"1": "您好"}
```