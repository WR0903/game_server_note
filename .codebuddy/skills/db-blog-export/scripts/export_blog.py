# -*- coding: utf-8 -*-
"""
从 SQLite 博客数据库导出文章为 Markdown，并整理图片到对应目录。

用法:
    python export_blog.py <db_path> [--output <output_dir>] [--images <image_dir1> <image_dir2> ...]

功能:
    1. 自动探查数据库，识别 blog 表及分类/图片引用
    2. 按分类建目录，每篇文章导出为一个 Markdown 文件
    3. 扫描文章中的图片引用，将本地图片复制到对应文章目录并更新引用
    4. 规范化 Markdown 表格格式
    5. 生成 README.md 目录索引（自动排除 .gitignore 中的目录）
"""

import sqlite3
import os
import re
import argparse
import shutil
from collections import OrderedDict

from normalize_tables import normalize_file as normalize_md_file

# ---- 工具函数 ----

INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def safe_name(name, fallback="untitled"):
    """清理文件名/目录名中的非法字符与保留名"""
    name = INVALID_CHARS.sub("_", str(name).strip())
    name = name.rstrip(". ")
    if not name:
        name = fallback
    stem = name.split(".")[0].upper()
    if stem in RESERVED_NAMES:
        name = "_" + name
    return name[:120]


def find_blog_table(cursor):
    """自动识别博客文章表，返回表名和字段映射"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cursor.fetchall()}

    # 常见表名
    for candidate in ("blog", "post", "article", "posts", "articles", "entry"):
        if candidate in tables:
            table = candidate
            break
    else:
        return None

    cursor.execute(f"PRAGMA table_info({table})")
    cols = {r[1].lower(): r[1] for r in cursor.fetchall()}

    # 字段映射：逻辑名 -> 实际列名
    field_map = {}
    for logic, candidates in [
        ("id", ["id"]),
        ("title", ["title", "name", "subject"]),
        ("text", ["text", "content", "body", "html"]),
        ("category", ["category", "cat", "category_id", "tag"]),
        ("created_at", ["created_at", "created", "date", "published_at", "pub_date", "timestamp"]),
        ("view_count", ["view_count", "views", "read_count", "hits"]),
        ("hidden", ["hidden", "draft", "is_draft", "published"]),
        ("pinned", ["pinned", "is_pinned", "sticky", "pin_weight"]),
        ("sort_order", ["sort_order", "sort", "order"]),
    ]:
        for c in candidates:
            if c in cols:
                field_map[logic] = cols[c]
                break

    # 必须有 id 和 text
    if "id" not in field_map or "text" not in field_map:
        return None

    return table, field_map


def find_category_table(cursor):
    """查找分类排序表"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cursor.fetchall()}
    for candidate in ("category_order", "category", "categories"):
        if candidate in tables:
            return candidate
    return None


def extract_image_refs(text):
    """从文章文本中提取图片引用，返回 [(文件名, 原始引用路径), ...]"""
    results = []
    if not text:
        return results

    # markdown 图片: ![alt](path)
    for m in re.finditer(r'!\[[^\]]*\]\(([^)]+)\)', text):
        path = m.group(1)
        if re.search(r'\.(png|jpg|jpeg|webp|gif|svg)', path, re.I):
            filename = os.path.basename(path)
            results.append((filename, path))

    # HTML img: <img src="path">
    for m in re.finditer(r'<img[^>]*src=["\']?([^"\'>\s]+)', text, re.I):
        path = m.group(1)
        if re.search(r'\.(png|jpg|jpeg|webp|gif|svg)', path, re.I):
            filename = os.path.basename(path)
            results.append((filename, path))

    return results


# ---- 核心流程 ----

def export_articles(db_path, output_dir):
    """
    导出文章为 Markdown 文件。
    返回 (导出数量, 文章信息列表) 其中文章信息 = {id, title, category, md_path, image_refs}
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    blog_info = find_blog_table(cur)
    if not blog_info:
        print("[ERROR] 无法识别博客文章表，请确认数据库结构")
        conn.close()
        return 0, []

    table, fm = blog_info

    # 分类排序
    cat_table = find_category_table(cur)
    cat_order = set()
    if cat_table:
        try:
            cur.execute(f"SELECT name FROM {cat_table} ORDER BY sort_order")
            cat_order = {r[0] for r in cur.fetchall()}
        except Exception:
            pass

    # 查询文章
    id_col = fm["id"]
    title_col = fm.get("title", id_col)
    text_col = fm["text"]
    cat_col = fm.get("category")
    created_col = fm.get("created_at")
    view_col = fm.get("view_count")
    hidden_col = fm.get("hidden")
    pinned_col = fm.get("pinned")
    sort_col = fm.get("sort_order")

    # 构建排序子句
    order_parts = []
    if cat_col:
        order_parts.append(cat_col)
    if pinned_col:
        order_parts.append(f"{pinned_col} DESC")
    if sort_col:
        order_parts.append(sort_col)
    order_parts.append(id_col)
    order_clause = ", ".join(order_parts)

    select_cols = [id_col, title_col, text_col]
    if cat_col:
        select_cols.append(cat_col)

    cur.execute(f"SELECT {', '.join(select_cols)} FROM {table} ORDER BY {order_clause}")
    rows = cur.fetchall()
    col_names = [d[0] for d in cur.description]

    # 按分类分组
    groups = OrderedDict()
    article_infos = []

    for row in rows:
        row_dict = dict(zip(col_names, row))
        article_id = row_dict[id_col]
        title = row_dict.get(title_col, f"无标题_{article_id}") or f"无标题_{article_id}"
        text = row_dict.get(text_col, "") or ""
        cat = row_dict.get(cat_col, "未分类") if cat_col else "未分类"
        cat = cat or "未分类"

        groups.setdefault(cat, []).append({
            "id": article_id, "title": title, "text": text, "category": cat,
        })

    # 排序分类
    ordered_cats = [c for c in cat_order if c in groups] + [c for c in groups if c not in cat_order]

    os.makedirs(output_dir, exist_ok=True)
    total = 0

    for cat in ordered_cats:
        items = groups[cat]
        safe_cat = safe_name(cat, "未分类")
        cat_dir = os.path.join(output_dir, safe_cat)
        os.makedirs(cat_dir, exist_ok=True)

        used_names = {}
        for idx, item in enumerate(items, 1):
            base = safe_name(item["title"], f"post_{item['id']}")
            fname = f"{idx:02d}_{base}.md"
            key = fname.lower()
            if key in used_names:
                fname = f"{idx:02d}_{base}_{item['id']}.md"
            used_names[fname.lower()] = True

            fp = os.path.join(cat_dir, fname)

            # 如原文不以标题开头，则补上 # 标题
            content = item["text"]
            prefix = ""
            if content and not content.lstrip().startswith("#"):
                prefix = f"# {item['title']}\n\n"

            with open(fp, "w", encoding="utf-8") as f:
                f.write(prefix)
                f.write(content)

            # 提取图片引用
            img_refs = extract_image_refs(content)

            article_infos.append({
                "id": item["id"],
                "title": item["title"],
                "category": cat,
                "md_path": fp,
                "cat_dir": cat_dir,
                "image_refs": img_refs,
            })
            total += 1

        print(f"  {cat:<20} {len(items):<4} 篇 -> {cat_dir}")

    conn.close()
    return total, article_infos


def organize_images(article_infos, image_dirs):
    """
    将本地图片文件复制到对应文章目录，并更新 Markdown 中的引用。
    image_dirs: 搜索图片的目录列表
    返回 (已处理数, 孤儿图片列表)
    """
    # 建立本地图片索引: filename -> filepath
    image_index = {}
    for d in image_dirs:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            fp = os.path.join(d, f)
            if os.path.isfile(fp) and re.search(r'\.(png|jpg|jpeg|webp|gif|svg)$', f, re.I):
                image_index[f] = fp

    if not image_index:
        print("  [WARN] 未找到任何图片文件")
        return 0, []

    # 建立图片 -> 文章的映射（基于文章引用）
    pic_to_articles = {}  # filename -> [article_info, ...]
    for info in article_infos:
        for filename, ref_path in info["image_refs"]:
            pic_to_articles.setdefault(filename, []).append(info)

    processed = 0
    used_pics = set()

    for filename, articles in pic_to_articles.items():
        if filename not in image_index:
            continue

        src = image_index[filename]
        used_pics.add(filename)

        for info in articles:
            dst = os.path.join(info["cat_dir"], filename)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)

            # 更新 Markdown 中的引用
            with open(info["md_path"], "r", encoding="utf-8") as f:
                content = f.read()

            # 替换 /static/uploads/filename 和任何包含 filename 的路径引用
            new_content = re.sub(
                r'!\[([^\]]*)\]\([^)]*[/\\]' + re.escape(filename) + r'\)',
                rf'![\1]({filename})',
                content
            )
            # 也处理 <img src="...filename...">
            new_content = re.sub(
                r'(<img[^>]*src=["\']?)[^"\'>\s]*[/\\]' + re.escape(filename) + r'(["\']?[^>]*>)',
                rf'\1{filename}\2',
                new_content
            )

            if new_content != content:
                with open(info["md_path"], "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"    [IMG] {info['category']}/{os.path.basename(info['md_path'])} -> {filename}")

            processed += 1

    # 孤儿图片（本地有但文章未引用）
    orphan = [f for f in image_index if f not in used_pics]
    return processed, orphan


def read_gitignore(output_dir):
    """读取 .gitignore，返回应忽略的目录名集合"""
    gitignore_path = os.path.join(output_dir, ".gitignore")
    ignored = set()
    if not os.path.isfile(gitignore_path):
        return ignored
    with open(gitignore_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # 只处理目录模式（以 / 结尾）
            if line.endswith("/"):
                ignored.add(line.rstrip("/"))
            # 也处理不带 / 的目录名
            elif "/" not in line and "." not in line:
                ignored.add(line)
    return ignored


def generate_readme(output_dir, article_infos):
    """生成 README.md 目录索引，排除 .gitignore 中的目录"""
    ignored_dirs = read_gitignore(output_dir)

    # 按分类收集文章
    cat_articles = OrderedDict()
    for info in article_infos:
        safe_cat = os.path.basename(info["cat_dir"])
        if safe_cat in ignored_dirs:
            continue
        cat_articles.setdefault(safe_cat, []).append(info)

    lines = ["# 博客文章归档\n"]

    # 顶部分类索引
    lines.append("## 目录\n")
    for cat in cat_articles:
        anchor = cat.lower().replace(" ", "-")
        lines.append(f"- [{cat}](#{anchor})")
    lines.append("")

    # 各分类文章列表
    for cat, articles in cat_articles.items():
        lines.append(f"### {cat}\n")
        for info in articles:
            rel_path = os.path.relpath(info["md_path"], output_dir)
            # 处理文件名中的空格：URL 编码
            rel_path_encoded = rel_path.replace(" ", "%20")
            # 显示名：去掉序号前缀
            display = os.path.basename(info["md_path"]).replace(".md", "")
            display = re.sub(r"^\d+_", "", display)
            lines.append(f"- [{display}]({rel_path_encoded})")
        lines.append("")

    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  已生成 {readme_path}（排除了 .gitignore 中的 {len(ignored_dirs)} 个目录）")


def main():
    parser = argparse.ArgumentParser(description="从 SQLite 博客数据库导出文章为 Markdown，并整理图片")
    parser.add_argument("db_path", help="SQLite 数据库文件路径")
    parser.add_argument("--output", "-o", default=".", help="输出目录（默认当前目录）")
    parser.add_argument("--images", "-i", nargs="*", default=["."], help="搜索图片的目录列表（默认当前目录）")
    args = parser.parse_args()

    if not os.path.exists(args.db_path):
        print(f"[ERROR] 数据库文件不存在: {args.db_path}")
        return

    print("=" * 60)
    print("步骤 1: 导出文章")
    print("=" * 60)
    total, article_infos = export_articles(args.db_path, args.output)
    print(f"\n共导出 {total} 篇文章到 {os.path.abspath(args.output)}")

    print("\n" + "=" * 60)
    print("步骤 2: 整理图片")
    print("=" * 60)
    img_count, orphan = organize_images(article_infos, args.images)
    print(f"\n已处理 {img_count} 处图片引用")

    if orphan:
        print(f"\n[注意] 以下 {len(orphan)} 张图片未被任何文章引用（孤儿图片）:")
        for f in orphan:
            print(f"  - {f}")

    print("\n" + "=" * 60)
    print("步骤 3: 规范化表格")
    print("=" * 60)
    norm_count = 0
    for info in article_infos:
        if normalize_md_file(info["md_path"]):
            norm_count += 1
    print(f"\n共规范化 {norm_count} 个文件的表格格式")

    print("\n" + "=" * 60)
    print("步骤 4: 生成 README.md")
    print("=" * 60)
    generate_readme(args.output, article_infos)

    print("\n完成!")


if __name__ == "__main__":
    main()
