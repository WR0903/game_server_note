# -*- coding: utf-8 -*-
"""
规范化 Markdown 文件中的表格：
- 缺表头分隔符的表格自动添加分隔行
- 统一分隔符格式为 | --- | --- |
- 跳过代码块、front matter
- 允许表格块内有最多 1 个空行（中间空行会被压缩）

使用: python normalize_tables.py [path ...]
    无参数时处理当前目录所有 .md 文件
"""
import os
import re
import sys


def parse_row(line):
    s = line.strip()
    inner = s[1:-1]
    cells = inner.split('|')
    return [c.strip() for c in cells]


def is_separator_row(line):
    s = line.strip()
    if not (s.startswith('|') and s.endswith('|')) or len(s) < 3:
        return False
    cells = parse_row(s)
    if not cells:
        return False
    return all(re.fullmatch(r':?-+:?', c) for c in cells)


def is_table_row(line):
    s = line.strip()
    return s.startswith('|') and s.endswith('|') and len(s) > 1


def format_separator(n):
    return '| ' + ' | '.join(['---'] * n) + ' |'


def collect_table_block(lines, start):
    """
    从 lines[start] 开始收集一个表格块。
    返回 (rows, end_index)，其中 rows 是 'row' / 'blank' 标记的元组列表。
    表格块终止条件：遇到 2 个连续空行 或 非表格非空行。
    """
    items = []
    j = start
    while j < len(lines):
        line = lines[j]
        if is_table_row(line):
            items.append(('row', line.rstrip('\n').rstrip('\r')))
            j += 1
        elif line.strip() == '':
            # 跳过连续空行，查看下一个非空行
            k = j
            while k < len(lines) and lines[k].strip() == '':
                k += 1
            if k < len(lines) and is_table_row(lines[k]):
                # 空行属于表格内部
                items.append(('blank', ''))
                j += 1
            else:
                # 表格结束
                break
        else:
            break

    # 去掉尾部空行
    while items and items[-1][0] == 'blank':
        items.pop()

    return items, j


def normalize_table_block(items):
    """规范化一个表格块"""
    rows = [item[1] for item in items if item[0] == 'row']
    if not rows:
        return [item[1] + '\n' for item in items]

    if len(rows) == 1:
        cols = len(parse_row(rows[0]))
        new_rows = [rows[0], format_separator(cols)]
    elif is_separator_row(rows[1]):
        header_cols = len(parse_row(rows[0]))
        new_rows = [rows[0], format_separator(header_cols)] + rows[2:]
    else:
        cols = len(parse_row(rows[0]))
        new_rows = [rows[0], format_separator(cols)] + rows[1:]

    return [r + '\n' for r in new_rows]


def normalize_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    i = 0
    in_code = False
    in_frontmatter = bool(lines) and lines[0].strip() == '---'

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # front matter
        if in_frontmatter:
            out.append(line)
            if stripped == '---':
                in_frontmatter = False
            i += 1
            continue

        # 代码块
        if stripped.startswith('```'):
            in_code = not in_code
            out.append(line)
            i += 1
            continue

        if in_code:
            out.append(line)
            i += 1
            continue

        # 表格行
        if is_table_row(line):
            items, j = collect_table_block(lines, i)
            out.extend(normalize_table_block(items))
            i = j
        else:
            out.append(line)
            i += 1

    new_content = ''.join(out)
    if new_content != ''.join(lines):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    targets = sys.argv[1:]
    if not targets:
        targets = ['.']

    md_files = []
    for t in targets:
        if os.path.isfile(t) and t.endswith('.md'):
            md_files.append(t)
        elif os.path.isdir(t):
            for root, dirs, files in os.walk(t):
                if '.codebuddy' in root.split(os.sep) or '.git' in root.split(os.sep):
                    continue
                for fn in files:
                    if fn.endswith('.md') and fn != 'README.md':
                        md_files.append(os.path.join(root, fn))

    changed = []
    for fp in md_files:
        if normalize_file(fp):
            changed.append(fp)

    print(f"已处理 {len(changed)} 个文件")
    for f in changed:
        print(f"  {f}")


if __name__ == "__main__":
    main()