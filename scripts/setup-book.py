#!/usr/bin/env python3
"""
中文经管统计类书籍 — 项目初始化向导。

用法：
    python setup-book.py
    python setup-book.py --from book-writing-projects.md --book 统计
"""

import argparse
import json
import re
import sys
from pathlib import Path


def slugify(title: str) -> str:
    """将中文书名转为 URL 安全的 slug（保留汉字拼音首字母风格）。"""
    # 简单方案：去掉特殊字符，用连字符连接
    return re.sub(r"[^\w\u4e00-\u9fff]+", "-", title.lower()).strip("-")


def find_book_projects_md() -> Path | None:
    """在常见位置查找 book-writing-projects.md。"""
    candidates = [
        Path.cwd() / ".workbuddy" / "book-projects" / "book-writing-projects.md",
        Path.home() / ".workbuddy" / "book-projects" / "book-writing-projects.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def parse_book_projects(md_path: Path) -> list:
    """解析 book-writing-projects.md，返回书籍创意列表。"""
    text = md_path.read_text(encoding="utf-8")
    books = []
    current = None

    for line in text.splitlines():
        m = re.match(r"## Book #\d+\s+(.+)$", line)
        if m:
            if current:
                books.append(current)
            current = {"title": m.group(1).strip(), "details": ""}
        elif current is not None:
            current["details"] += line + "\n"
    if current:
        books.append(current)

    return books


def interactive_setup() -> dict:
    """交互式问答，收集书籍元数据。"""
    print("\n📚 书籍项目初始化向导\n" + "-" * 40)

    title = input("书名（工作书名）：").strip()
    if not title:
        print("错误：书名是必填项。")
        sys.exit(1)

    subtitle = input("副标题（可选）：").strip()
    author = input("作者名：").strip() or "作者"
    topic = input("核心主题/本书解决的核心问题：").strip() or title
    target_audience = input("目标读者（谁会读这本书？）：").strip() or "经管类专业学生"

    print("\n书型（二选一）：")
    print("  [1] 经管类统计学教材（结构严谨，含例题、习题、Stata 代码）")
    print("  [2] 经管类统计学科普读物（通俗易懂，案例驱动，面向职场人士）")
    book_type_choice = input("请选择 [1]：").strip() or "1"
    book_type = "stats-popular" if book_type_choice == "2" else "stats-textbook"

    description = input("一句话简介（可选）：").strip() or ""

    print("\n章节规划（逐行输入章节标题，空行结束）：")
    chapters = []
    toc_items = []
    while True:
        ch = input(f"  第 {len(chapters)+1} 章标题：").strip()
        if not ch:
            break
        slug = slugify(ch)
        fname = f"ch{len(chapters)+1:02d}-{slug}.md"
        chapters.append(fname)
        toc_items.append(ch)

    if not chapters:
        print("错误：至少需要规划一个章节。")
        sys.exit(1)

    cover = input("封面图片路径（可选，可直接回车跳过）：").strip()
    kdp_select = input("是否在亚马逊 KDP 独家发布？[y/N]：").strip().lower() == "y"
    publisher = input("出版社名（可选，KDP 出版时填写）：").strip()

    slug = slugify(title)
    workspace = input(f"项目目录名 [{slug}/]：").strip()
    if not workspace:
        workspace = slug

    return {
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "topic": topic,
        "target_audience": target_audience,
        "book_type": book_type,
        "description": description,
        "chapters": chapters,
        "toc_items": toc_items,
        "cover_image": cover,
        "workspace": workspace,
        "slug": slug,
        "kdp_select": kdp_select,
        "publisher": publisher,
        "categories": [],
        "language": "zh-CN",
    }


def from_existing_project(md_path: Path, book_keyword: str) -> dict:
    """从已有的 book-writing-projects.md 中读取书籍创意。"""
    books = parse_book_projects(md_path)
    if not books:
        print(f"错误：在 {md_path} 中未找到任何书籍项目。")
        sys.exit(1)

    match = None
    for b in books:
        if book_keyword.lower() in b["title"].lower():
            match = b
            break

    if not match:
        print(f"\n可用的书籍项目：")
        for i, b in enumerate(books):
            print(f"  [{i+1}] {b['title']}")
        choice = input("\n请选择（输入序号）[1]：").strip() or "1"
        match = books[int(choice) - 1]

    title = match["title"]
    slug = slugify(title)
    topic = match.get("details", "").strip()[:80] or title

    print(f"\n📖 已选择：《{title}》")
    subtitle = input("副标题（可选）：").strip()
    author = input("作者名：").strip() or "作者"
    target_audience = input("目标读者：").strip() or "经管类专业学生"
    description = input("一句话简介（可选）：").strip() or ""

    print("\n书型（二选一）：")
    print("  [1] 经管类统计学教材")
    print("  [2] 经管类统计学科普读物")
    book_type_choice = input("请选择 [1]：").strip() or "1"
    book_type = "stats-popular" if book_type_choice == "2" else "stats-textbook"

    details = match.get("details", "")
    suggested_chapters = re.findall(r"[-*]\s*\*\*(.+?)\*\*", details)
    if not suggested_chapters:
        suggested_chapters = re.findall(r"[-*]\s*(.+)", details)[:10]

    chapters = []
    toc_items = []
    if suggested_chapters:
        print(f"\n从项目文件中提取到的章节建议：")
        for i, ch in enumerate(suggested_chapters):
            print(f"  {i+1}. {ch}")
        use = input("\n是否使用这些章节？[Y/n]：").strip().lower()
        if use != "n":
            for i, ch in enumerate(suggested_chapters):
                ch_slug = slugify(ch)
                fname = f"ch{i+1:02d}-{ch_slug}.md"
                chapters.append(fname)
                toc_items.append(ch)

    if not chapters:
        print("\n请手动输入章节标题（空行结束）：")
        while True:
            ch = input(f"  第 {len(chapters)+1} 章标题：").strip()
            if not ch:
                break
            ch_slug = slugify(ch)
            fname = f"ch{len(chapters)+1:02d}-{ch_slug}.md"
            chapters.append(fname)
            toc_items.append(ch)

    if not chapters:
        print("错误：至少需要规划一个章节。")
        sys.exit(1)

    kdp_select = input("是否在亚马逊 KDP 独家发布？[y/N]：").strip().lower() == "y"
    publisher = input("出版社名（可选）：").strip()

    workspace = slug
    return {
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "topic": topic,
        "target_audience": target_audience,
        "book_type": book_type,
        "description": description,
        "chapters": chapters,
        "toc_items": toc_items,
        "cover_image": "",
        "workspace": workspace,
        "slug": slug,
        "kdp_select": kdp_select,
        "publisher": publisher,
        "categories": [],
        "language": "zh-CN",
    }


def create_project_files(data: dict):
    """创建项目目录和所有必要文件。"""
    ws = Path(data["workspace"]).expanduser().resolve()
    ws.mkdir(parents=True, exist_ok=True)
    chapters_dir = ws / "chapters"
    chapters_dir.mkdir(exist_ok=True)
    output_dir = ws / (data.get("output_dir") or "Book-Output")
    output_dir.mkdir(exist_ok=True)

    config = {
        "workspace": ".",
        "chapters_dir": "chapters",
        "output_dir": "Book-Output",
        "cover_image": data.get("cover_image", ""),
        "chapters": data["chapters"],
        "title": data["title"],
        "subtitle": data.get("subtitle", ""),
        "author": data["author"],
        "topic": data.get("topic", data["title"]),
        "target_audience": data.get("target_audience", ""),
        "book_type": data.get("book_type", "stats-textbook"),
        "description": data.get("description", ""),
        "kdp_select": data.get("kdp_select", False),
        "publisher": data.get("publisher", ""),
        "categories": data.get("categories", []),
        "language": data.get("language", "zh-CN"),
        "toc_items": data["toc_items"],
        "slug": data["slug"],
    }
    config_path = ws / "book-config.json"
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    print(f"\n✅ 已创建：{config_path}")

    outline_path = ws / "outline.md"
    if not outline_path.exists():
        lines = [
            f"# {data['title']} — 内容大纲\n",
            f"**副标题：** {data.get('subtitle', '')}\n",
            f"**作者：** {data['author']}\n",
            f"**简介：** {data.get('description', '')}\n",
            "\n---\n",
        ]
        for i, (ch, toc) in enumerate(zip(data["chapters"], data["toc_items"]), 1):
            lines.append(f"\n## 第 {i} 章：{toc}\n")
            lines.append(f"- [ ] 核心知识点 1\n")
            lines.append(f"- [ ] 核心知识点 2\n")
            lines.append(f"- [ ] 核心知识点 3\n")
            if config["book_type"] == "stats-textbook":
                lines.append(f"- 目标字数：3,000–5,000 字\n")
            else:
                lines.append(f"- 目标字数：2,000–3,500 字\n")
        outline_path.write_text("".join(lines), encoding="utf-8")
        print(f"✅ 已创建：{outline_path}")

    sample_path = chapters_dir / data["chapters"][0]
    if not sample_path.exists():
        is_textbook = config["book_type"] == "stats-textbook"
        if is_textbook:
            tmpl = f"""# 第 1 章：{data['toc_items'][0] if data['toc_items'] else '导论'}

## 引例
{{{{ 用一则经管实证场景引入本章主题，1–2 段，150–250 字。 }}}}

## 1.1 节标题
{{{{ 正文，350–600 字，配 1–2 个例题。 }}}}

### 例 1-1 例题标题
**题目描述：** {{{{ 背景描述 }}}}
**Stata 代码：**
```stata
{{{ Stata 命令 }}}
```
**输出结果：**
{{{{ 回归表或描述统计表（Markdown 表格）}}}}
**结果解读：**
{{{{ 对输出结果的经管意义解释，2–3 段 }}}}

## 1.2 节标题
{{{{ 正文 }}}}

## 本章小结
● {{{{ 要点 1 }}}}
● {{{{ 要点 2 }}}}
● {{{{ 要点 3 }}}}

## 习题
1. {{{{ 计算题或实操题，注明数据来源 }}}}
2. ...
"""
        else:
            tmpl = f"""# 第 1 章：{data['toc_items'][0] if data['toc_items'] else '开篇'}

{{{{ 开篇场景，2–3 段，直接讲一个读者可能遇到过的困扰或误会。 }}}}

## {{{{ 核心概念，用口语化标题 }}}}
{{{{ 解释，短段落，300 字以内一节，多用项目符号 }}}}

> **一句话记住：** {{{{ 关键要点 }}}}

## {{{{ 下一个概念 }}}}

**本章行动清单：**
1. {{{{ 具体可操作的步骤 }}}}
2. {{{{ 具体可操作的步骤 }}}}
"""
        sample_path.write_text(tmpl, encoding="utf-8")
        print(f"✅ 已创建示例章节：{sample_path}")

    skill_dir = Path(__file__).resolve().parent.parent
    print(f"\n📁 项目目录：{ws}")
    print(f"📄 配置文件：{config_path.name}")
    print(f"📝 大纲文件：{outline_path.name}")
    print(f"📂 章节目录：{chapters_dir}")
    print(f"\n下一步：")
    print(f"  1. 编辑 outline.md，细化各章知识点")
    print(f"  2. 逐章写作（建议通过 AI 多轮对话完成）")
    print(f"  3. 生成 KDP 元数据（如需出版到亚马逊）：")
    print(f"     python \"{skill_dir}/scripts/generate-kdp-metadata.py\" --project \"{ws}\"")
    print(f"  4. 运行 merge-book.py 生成 HTML + PDF：")
    print(f"     python \"{skill_dir}/scripts/merge-book.py\" --project \"{ws}\"")


def main():
    parser = argparse.ArgumentParser(description="中文经管统计类书籍 — 项目初始化向导")
    parser.add_argument("--from", dest="md_file", default=None,
                        help="book-writing-projects.md 的路径")
    parser.add_argument("--book", default=None,
                        help="在 md 文件中匹配书名的关键词")
    args = parser.parse_args()

    if args.md_file or args.book:
        md_path = Path(args.md_file) if args.md_file else find_book_projects_md()
        if not md_path or not md_path.exists():
            print("错误：未找到 book-writing-projects.md。")
            print("  搜索路径：.workbuddy/book-projects/book-writing-projects.md")
            sys.exit(1)
        data = from_existing_project(md_path, args.book or "")
    else:
        data = interactive_setup()

    print(f"\n📋 请确认书籍配置：")
    print(f"  书名：     {data['title']}")
    print(f"  副标题：   {data.get('subtitle', '')}")
    print(f"  作者：     {data['author']}")
    print(f"  书型：     {'经管类统计学教材' if data['book_type'] == 'stats-textbook' else '经管类统计学科普读物'}")
    print(f"  章节数：   {len(data['chapters'])}")
    print(f"  项目目录： {data['workspace']}")
    confirm = input("\n确认创建项目？[Y/n]：").strip().lower()
    if confirm == "n":
        print("已取消。")
        sys.exit(0)

    create_project_files(data)


if __name__ == "__main__":
    main()
