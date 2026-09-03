---
title: vscode 远程调试c++
category: C++
created_at: 2026-04-26 12:31:09
view_count: 1
---

# vscode 远程调试c++

## 首先vscode安装ssh扩展
安装完成后ssh上去

## 安装c++相关扩展和gdb相关扩展

配置launch.json文件

```
{
    "configurations": [
        {
            "name": "game",
            "type": "cppdbg",
            "request": "attach",
            "program": "${workspaceFolder}/bin/gamed",
            "MIMode": "gdb",
            "setupCommands": [
                {
                    "description": "为 gdb 启用整齐打印",
                    "text": "-enable-pretty-printing",
                    "ignoreFailures": true
                },
                {
                    "description": "将反汇编风格设置为 Intel",
                    "text": "-gdb-set disassembly-flavor intel",
                    "ignoreFailures": true
                }
            ]
        },

    ]
}
```

