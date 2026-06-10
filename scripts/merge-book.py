#!/usr/bin/env python3
"""
中文经管统计类书籍 — Markdown 章节合并器。

用法：
    python merge-book.py                          # 自动查找 book-config.json
    python merge-book.py --config /path/to/config.json   # 手动指定
    python merge-book.py --project /path/to/project      # 指定项目目录

配置文件自动发现（按优先级）：
  1. --config 参数（如提供）
  2. --project 参数指定的目录中的 book-config.json
  3. 当前工作目录下的 book-config.json
  4. .workbuddy/book-projects/*/book-config.json
  5. 脚本所在目录的 book-config.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ── 默认配置 ──────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "workspace": ".",
    "chapters_dir": "chapters",
    "output_dir": "Book-Output",
    "cover_image": "",
    "chapters": [],
    "title": "书名",
    "subtitle": "副标题",
    "author": "作者",
    "description": "一本统计学专业书籍。",
    "toc_items": [],
    "slug": "",
    "language": "zh-CN",
}


# ── 配置文件自动发现 ─────────────────────────────────────────────────────

def find_config(project_dir=None) -> str | None:
    """
    自动查找 book-config.json。
    返回配置文件路径，未找到则返回 None。
    """
    candidates = []

    # 1. project_dir/book-config.json（如果提供了 --project）
    if project_dir:
        p = Path(project_dir).expanduser().resolve() / "book-config.json"
        if p.exists():
            candidates.append(str(p))

    # 2. ./book-config.json（当前工作目录）
    p = Path.cwd() / "book-config.json"
    if p.exists():
        candidates.append(str(p))

    # 3. .workbuddy/book-projects/*/book-config.json
    wb_root = Path.cwd()
    for parent in [wb_root] + list(wb_root.parents):
        wbp = parent / ".workbuddy" / "book-projects"
        if wbp.exists():
            for sub in sorted(wbp.iterdir()):
                cfg = sub / "book-config.json"
                if cfg.exists():
                    candidates.append(str(cfg))
            break

    # 4. 脚本所在目录的 book-config.json
    script_dir = Path(__file__).resolve().parent.parent
    p = script_dir / "book-config.json"
    if p.exists():
        candidates.append(str(p))

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # 找到多个时列出供用户选择
    print("\n找到多个 book-config.json 文件：")
    for i, c in enumerate(candidates):
        print(f"  [{i+1}] {c}")
    print()
    while True:
        try:
            choice = input("请选择配置文件 [1]：").strip() or "1"
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                return candidates[idx]
        except (ValueError, IndexError):
            print(f"  请输入 1 到 {len(candidates)} 之间的数字")
        except EOFError:
            print(f"  非交互模式：使用 [1] {candidates[0]}\n")
            return candidates[0]


# ── Markdown → HTML 转换 ───────────────────────────────────────────────────

def md_to_html(text: str) -> str:
    """将基础 Markdown 转换为 HTML。"""
    html = text

    # 转义 HTML 特殊字符（顺序很重要）
    html = html.replace("&", "&amp;")
    html = html.replace("<", "&lt;")
    html = html.replace(">", "&gt;")

    # 代码块（```lang\n...```）
    html = re.sub(
        r"```(\w*)\n(.*?)```",
        r"<pre><code>\2</code></pre>",
        html,
        flags=re.DOTALL,
    )
    # 行内代码
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

    # 标题（支持文件开头和正文中出现的情况）
    for lvl in [1, 2, 3, 4]:
        hashes = "#" * lvl
        html = re.sub(
            rf"(?:^|\n){hashes} (.+?)(?:\n|$)",
            lambda m: f"\n<h{lvl}>{m.group(1).strip()}</h{lvl}>\n",
            html,
            flags=re.MULTILINE,
        )

    # 粗体 / 斜体
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    # 水平线
    html = re.sub(r"\n---+\n", "\n<hr>\n", html)

    # 引用块
    html = re.sub(r"\n> (.+)", r"<blockquote>\1</blockquote>", html)

    # 无序列表
    html = re.sub(
        r"(^[-*] .+$\n?)+",
        lambda m: (
            "<ul>"
            + re.sub(r"^[-*] (.+)$", r"<li>\1</li>", m.group(), flags=re.MULTILINE)
            + "</ul>"
        ),
        html,
        flags=re.MULTILINE,
    )

    # 有序列表
    html = re.sub(
        r"(^\d+\. .+$\n?)+",
        lambda m: (
            "<ol>"
            + re.sub(r"^\d+\. (.+)$", r"<li>\1</li>", m.group(), flags=re.MULTILINE)
            + "</ol>"
        ),
        html,
        flags=re.MULTILINE,
    )

    # 表格
    html = _convert_tables(html)

    # 段落（包裹未被 HTML 标签标记的连续文本行）
    html = re.sub(r"\n([^<\n][^\n]+)\n\n", r"\n<p>\1</p>\n", html)

    return html


def _convert_tables(text: str) -> str:
    """将简单 Markdown 表格转换为 HTML 表格。"""
    table_pattern = re.compile(
        r"(\|.+\|\n\|[-| :]+\|\n)((?:\|.+\|\n)+)",
        re.MULTILINE,
    )

    def build_table(m):
        rows = m.group(2).strip().split("\n")
        header = rows[0] if rows else ""
        body_rows = rows[1:] if len(rows) > 1 else []

        def row_to_cells(row, tag):
            cells = [c.strip() for c in row.strip("|").split("|")]
            cells = [re.sub(r"^#{1,4}\s+", "", c) for c in cells]
            return "".join(f"<{tag}>{c}</{tag}>" for c in cells)

        header_html = f"<thead><tr>{row_to_cells(header, 'th')}</tr></thead>"
        body_html = "<tbody>"
        for r in body_rows:
            body_html += f"<tr>{row_to_cells(r, 'td')}</tr>"
        body_html += "</tbody>"

        return f"<table>{header_html}{body_html}</table>"

    return table_pattern.sub(build_table, text)


# ── HTML 文档构建器 ─────────────────────────────────────────────────────

def build_full_html(chapters_html: list, config: dict) -> str:
    """将所有章节包裹为完整的 HTML 文档。"""
    cover_img = config.get("cover_image", "")
    title = config.get("title", "书名")
    subtitle = config.get("subtitle", "")
    author = config.get("author", "作者")
    description = config.get("description", "")
    toc_items = config.get("toc_items", [])
    language = config.get("language", "zh-CN")

    chapters_str = "\n".join(chapters_html)

    cover_img_tag = (
        f'<img src="{cover_img}" '
        'alt="封面" '
        'style="width:55%; max-width:380px; display:block; margin:0 auto 1.5rem; '
        'border-radius:4px; box-shadow:0 4px 20px rgba(0,0,0,0.12);" />'
        if cover_img else ""
    )

    toc_rows = "".join(
        f"    <li><span>{item}</span></li>\n"
        for item in toc_items
    )

    back_cover_img_tag = (
        f'<img src="{cover_img}" alt="封面" '
        'style="width:40%; max-width:280px; border-radius:4px; '
        'box-shadow:0 4px 16px rgba(0,0,0,0.12); margin:0 auto 2rem; display:block;" />'
        if cover_img else ""
    )

    has_cover_cls = " has-cover" if cover_img else ""

    return f"""<!DOCTYPE html>
<html lang="{language}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Source Han Serif SC", "Noto Serif CJK SC", "SimSun", Georgia, serif;
    font-size: 11pt;
    line-height: 1.75;
    color: #2c2c2c;
    background: #fff;
    max-width: 700px;
    margin: 0 auto;
    padding: 3rem 2rem 6rem;
  }}

  /* 封面页 */
  .cover {{
    text-align: center;
    padding: 4rem 0 3rem;
    border-bottom: 2px solid #2c2c2c;
    margin-bottom: 3rem;
  }}
  .cover-title {{
    font-size: 2.4rem;
    font-weight: bold;
    letter-spacing: -0.5px;
    line-height: 1.2;
    color: #1a1a2e;
    margin: 1.5rem 0 0.5rem;
  }}
  .cover-subtitle {{
    font-size: 1.1rem;
    color: #555;
    font-style: italic;
    margin-bottom: 2rem;
  }}
  .cover-note {{
    font-size: 0.85rem;
    color: #888;
    margin-top: 2rem;
  }}
  .cover.has-cover .cover-title,
  .cover.has-cover .cover-subtitle {{
    display: none;
  }}

  /* 目录 */
  .toc {{
    page-break-after: always;
    margin-bottom: 3rem;
  }}
  .toc h2 {{
    font-size: 1.4rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.3rem;
  }}
  .toc ol {{ counter-reset: chapter; list-style: none; padding-left: 0; }}
  .toc li {{
    counter-increment: chapter;
    margin: 0.4rem 0;
    display: flex;
    justify-content: space-between;
    font-size: 1rem;
  }}
  .toc li::before {{
    content: counter(chapter) ". ";
    font-weight: bold;
    min-width: 2rem;
  }}
  .toc li span {{ flex: 1; padding-left: 0.5rem; }}

  /* 章节标题 */
  h1 {{
    font-size: 1.8rem;
    margin: 2.5rem 0 1.5rem;
    color: #1a1a2e;
    border-bottom: 3px solid #e8a0bf;
    padding-bottom: 0.4rem;
    page-break-before: always;
  }}
  h2 {{
    font-size: 1.25rem;
    margin: 2rem 0 0.8rem;
    color: #2a2a5e;
    font-weight: bold;
  }}
  h3 {{
    font-size: 1.05rem;
    margin: 1.5rem 0 0.5rem;
    color: #333;
    font-weight: bold;
  }}

  /* 正文段落 */
  p {{ margin: 0 0 1rem; orphans: 3; widows: 3; }}
  .lead {{
    font-size: 1.15rem;
    color: #444;
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }}

  /* 列表 */
  ul, ol {{ margin: 0.5rem 0 1rem 1.5rem; }}
  li {{ margin: 0.25rem 0; }}

  /* 引用块 */
  blockquote {{
    border-left: 4px solid #e8a0bf;
    margin: 1.5rem 0;
    padding: 0.8rem 1.2rem;
    background: #fdf4f8;
    font-style: italic;
  }}

  /* 表格 */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.2rem 0;
    font-size: 0.9rem;
  }}
  th {{
    background: #2a2a5e;
    color: #fff;
    padding: 0.5rem 0.7rem;
    text-align: left;
    font-weight: bold;
  }}
  td {{
    padding: 0.4rem 0.7rem;
    border-bottom: 1px solid #e0e0e0;
  }}
  tr:nth-child(even) td {{ background: #f9f4f9; }}

  /* 章节结束标识 */
  .chapter-end {{
    text-align: center;
    margin: 2.5rem 0;
    color: #ccc;
    font-size: 1.5rem;
    letter-spacing: 0.5rem;
  }}

  /* 行动清单 / 要点框 */
  .action-box {{
    background: #f0f4ff;
    border: 2px solid #4a6fa5;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin: 1.5rem 0;
  }}
  .action-box strong {{ color: #2a2a5e; display: block; margin-bottom: 0.4rem; }}

  /* 打印样式 */
  @media print {{
    h1 {{ page-break-before: always; }}
    .cover {{ page-break-after: always; }}
  }}
</style>
</head>
<body>

<!-- ══ 封面 ═════════════════════════════════════════════════ -->
<div class="cover{has_cover_cls}">
  {cover_img_tag}
  <div class="cover-title">{title}</div>
  <div class="cover-subtitle">{subtitle}</div>
  <p style="color:#666; font-size:1rem; max-width:480px; margin:0 auto 1.5rem;
             font-style:italic; line-height:1.6;">
    {description}
  </p>
  <p class="cover-note">{author}</p>
</div>

<!-- ══ 目录 ══════════════════════════════════════════════════ -->
<div class="toc">
  <h2>目录</h2>
  <ol>
{toc_rows}  </ol>
</div>

<!-- ══ 正文章节 ════════════════════════════════════════════════ -->
{chapters_str}

<!-- ══ 封底 ══════════════════════════════════════════════ -->
<div style="page-break-before:always; text-align:center; padding:4rem 0;
             border-top:2px solid #2c2c2c; margin-top:3rem;">
  <p style="font-size:1.3rem; font-weight:bold; color:#1a1a2e;
             margin-bottom:1rem;">{title}</p>
  <p style="font-size:1rem; color:#555; font-style:italic; margin-bottom:2rem;">
    {subtitle}
  </p>
  {back_cover_img_tag}
  <p style="font-size:0.85rem; color:#888; max-width:400px; margin:0 auto;
             line-height:1.6;">
    本书仅供教学与学习参考。统计数据的解读须结合具体经管场景，
    不构成专业投资建议。如需引用书中数据或方法，请注明出处。
  </p>
</div>

</body>
</html>"""


# ── 配置加载器 ──────────────────────────────────────────────────────────

def load_config(config_path: str) -> dict:
    """加载配置文件并与默认配置合并。"""
    path = Path(config_path)
    if not path.exists():
        print(f"错误：配置文件不存在：{config_path}")
        sys.exit(1)

    user_config = json.loads(path.read_text(encoding="utf-8"))
    cfg = {**DEFAULT_CONFIG, **user_config}

    base = path.parent.resolve()
    ws = (base / cfg["workspace"]).resolve()

    cfg["_workspace"] = ws
    cfg["_chapters_dir"] = (
        (base / cfg["chapters_dir"]).resolve()
        if not Path(cfg["chapters_dir"]).is_absolute()
        else Path(cfg["chapters_dir"])
    )
    cfg["_output_dir"] = (
        (base / cfg["output_dir"]).resolve()
        if not Path(cfg["output_dir"]).is_absolute()
        else Path(cfg["output_dir"])
    )
    if cfg.get("cover_image"):
        cfg["cover_image"] = str(
            (base / cfg["cover_image"]).resolve()
            if not Path(cfg["cover_image"]).is_absolute()
            else Path(cfg["cover_image"])
        )

    slug = cfg.get("slug", "").strip()
    if not slug:
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", cfg["title"].lower()).strip("-")
    cfg["_slug"] = slug

    return cfg


# ── 主程序 ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="中文经管统计类书籍 — Markdown 章节合并器"
    )
    parser.add_argument("--config", default=None, help="book-config.json 的路径（默认：自动发现）")
    parser.add_argument("--project", default=None, help="包含 book-config.json 的项目目录")
    args = parser.parse_args()

    config_path = None
    if args.config:
        config_path = args.config
        print(f"使用配置文件：{config_path}")
    else:
        config_path = find_config(project_dir=args.project)
        if not config_path:
            print("错误：未找到 book-config.json。")
            print("\n搜索路径：")
            print("  1. --project <目录>/book-config.json")
            print("  2. ./book-config.json")
            print("  3. .workbuddy/book-projects/*/book-config.json")
            print("  4. 脚本所在目录/book-config.json")
            print("\n提示：请先运行 python setup-book.py 创建书籍项目。")
            sys.exit(1)
        print(f"找到配置文件：{config_path}")

    cfg = load_config(config_path)

    ws = cfg["_workspace"]
    chapters_dir = cfg["_chapters_dir"]
    output_dir = cfg["_output_dir"]
    output_dir.mkdir(exist_ok=True, parents=True)

    print(f"\n项目目录：  {ws}")
    print(f"章节目录：  {chapters_dir}")
    print(f"输出目录：  {output_dir}")
    print()

    # 1. 转换所有章节
    chapters_html = []
    for fname in cfg["chapters"]:
        path = chapters_dir / fname
        if path.exists():
            html = md_to_html(path.read_text(encoding="utf-8"))
            chapters_html.append(html)
            print(f"  ✓ {fname}")
        else:
            print(f"  ✗ 缺失：{fname}")

    if not chapters_html:
        print("\n未找到任何章节文件，请检查配置文件。")
        sys.exit(1)

    # 2. 构建完整 HTML
    full_html = build_full_html(chapters_html, cfg)
    html_path = output_dir / f"{cfg['_slug']}.html"
    html_path.write_text(full_html, encoding="utf-8")
    print(f"\n  HTML → {html_path}")

    # 3. 使用 Playwright 生成 PDF
    try:
        from playwright.sync_api import sync_playwright

        pdf_path = output_dir / f"{cfg['_slug']}.pdf"
        print("\n  正在使用 Playwright 生成 PDF...")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                margin={"top": "2cm", "bottom": "2cm",
                        "left": "2.5cm", "right": "2.5cm"},
                print_background=True,
                display_header_footer=False,
            )
            browser.close()

        print(f"  PDF → {pdf_path}")

    except ImportError:
        print("\n  ⚠ Playwright 未安装，跳过 PDF 生成。安装方式：")
        print("    pip install playwright && playwright install chromium")
        print("  HTML 已生成，安装 Playwright 后重新运行即可生成 PDF。")

    print(f"\n✅ 完成！")
    print(f"   HTML 文件：{html_path}")
    if "pdf_path" in dir():
        print(f"   PDF  文件：{pdf_path}")


if __name__ == "__main__":
    main()
