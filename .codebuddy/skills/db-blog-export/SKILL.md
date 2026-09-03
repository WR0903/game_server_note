---
name: db-blog-export
description: 从 SQLite 博客数据库（如 Flask 博客）提取文章为分类目录下的 Markdown 文档，自动整理文章引用的图片到对应目录，并更新文档中的图片引用路径。此技能适用于用户拥有博客数据库文件（如 data.db）并希望将内容导出为本地 Markdown 文件结构的场景。触发条件：用户提到从数据库提取/导出博客文章、把博客数据库转成 Markdown、整理博客文章图片、或提供了 .db 文件要求提取文章内容。
---

# DB Blog Export

## Overview

从 SQLite 博客数据库中提取文章，导出为按分类组织的 Markdown 文件结构，并自动将文章引用的本地图片整理到对应文章目录下。

## Workflow

### Step 1: 探查数据库

1. 打开用户指定的 SQLite 数据库文件
2. 自动识别博客文章表（支持 blog/post/article 等常见表名）
3. 自动映射字段（id、title、text/content、category、created_at 等）
4. 识别分类排序表（如 category_order）
5. 报告发现的表结构、文章数量和分类列表

### Step 2: 导出文章

运行 `scripts/export_blog.py` 的导出逻辑：

1. 按分类创建目录（目录名经安全字符处理）
2. 每篇文章导出为一个 Markdown 文件，命名格式 `序号_标题.md`
3. 文件头部添加 YAML front matter（title、category、created_at、view_count、hidden）
4. 正文保留数据库中的原始 Markdown/HTML 内容
5. 文章按分类、置顶、排序字段排序

### Step 3: 整理图片

1. 扫描所有导出文章中的图片引用（markdown `![](path)` 和 HTML `<img src="...">`）
2. 在用户指定的图片目录中查找匹配的本地图片文件
3. 将匹配的图片复制到对应文章所在目录
4. 更新 Markdown 中的图片引用路径为本地相对路径（如 `![alt](image.png)`）
5. 报告孤儿图片（本地存在但未被任何文章引用的图片）

## Usage

### 一键导出（推荐）

使用 `scripts/export_blog.py` 脚本一次性完成文章导出和图片整理：

```bash
python scripts/export_blog.py data.db --output . --images .
```

参数说明：
- `db_path`: SQLite 数据库文件路径（必需）
- `--output / -o`: 输出目录，分类目录直接创建在此目录下（默认当前目录）
- `--images / -i`: 搜索图片文件的目录列表（默认当前目录）

### 手动步骤

如果需要分步执行或自定义处理：

1. **探查数据库结构**：先读取数据库表结构和字段，确认 blog 表和字段映射
2. **导出文章**：执行导出脚本的文章导出部分
3. **整理图片**：确认图片文件位置后，执行图片整理部分

## Notes

- 文章正文中的原始 Markdown 内容不做修改（仅图片路径会被更新）
- 文件名中包含 Windows 非法字符时自动替换为下划线
- 分类目录名同样进行安全字符处理
- 孤儿图片（未被引用的本地图片文件）会在输出中列出，由用户决定处置
- 外部 URL 图片（如 CSDN、腾讯云等）保持原样不处理
