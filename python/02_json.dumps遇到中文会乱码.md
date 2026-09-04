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
