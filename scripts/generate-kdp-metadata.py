#!/usr/bin/env python3
"""
中文经管统计类书籍 — 亚马逊 KDP 出版元数据生成器。

用法：
    python generate-kdp-metadata.py
    python generate-kdp-metadata.py --config /path/to/book-config.json
    python generate-kdp-metadata.py --project /path/to/project-dir

输出：
    {项目目录}/kdp-metadata.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ── KDP 常量 ──────────────────────────────────────────────────────────

MAX_DESCRIPTION_CHARS = 4000
MAX_KEYWORDS = 7
TITLE_SUBTITLE_MAX = 200

# 经管统计类关键词池
COMMON_KEYWORDS = {
    "stats_textbook": "统计学教材, Stata 实操, 经管统计, 回归分析, 数据分析",
    "stats_popular": "统计思维, 数据解读, 商业分析, 经管科普, 数据分析入门",
    "regression": "回归分析, 面板数据, OLS, 计量经济学",
    "descriptive": "描述性统计, 数据可视化,  summary statistics",
    "inference": "统计推断, 假设检验, 置信区间, p值",
    "teaching": "统计学教学, 经管课程, 实验教学, 课程设计",
    "business": "商务数据分析, 商业统计, 经管决策, 数据驱动",
    "software": "Stata 教程, 统计软件, do 文件, 代码复现",
}

# 描述模板（按 book_type 区分）
DESCRIPTION_TEMPLATES = {
    "stats-textbook": (
        "<p><b>本书特色：</b></p>"
        "<ul>"
        "<li>每章配有引例、例题（含完整 Stata 代码）和习题</li>"
        "<li>关键术语首次出现时附英文原文，方便对照阅读</li>"
        "<li>例题数据均来自公开宏观数据库（CEIC/iCPI 等），可直接复现</li>"
        "<li>习题含上机操作题，适合经管类本科实验教学</li>"
        "</ul>"
        "<p>本书适用于经管类本科生、研究生，以及需要运用 Stata 进行数据分析的研究人员。</p>"
        "<p><b>涵盖内容：</b>{topic}，从基础描述统计到多元回归、面板数据及稳健性检验。</p>"
    ),
    "stats-popular": (
        "<p><b>不懂公式也能读懂统计——这本书就是为你写的。</b></p>"
        "<p>你是不是也有过这种时刻：看到回归结果里的 t 值，不知道该不该相信？"
        "拿到一组数据，不知道该用 t 检验还是 Wilcoxon？"
        "这本书不教你背公式，而是用真实的商业场景，帮你建立统计直觉。</p>"
        "<p><b>你将读到：</b></p>"
        "<ul>"
        "<li>用定价策略理解回归系数——不用公式，用常识</li>"
        "<li>用 A/B 测试理解假设检验——你每天都在做，只是没意识到</li>"
        "<li>用真实财报数据理解相关与因果——避免经管研究中最常见的坑</li>"
        "</ul>"
        "<p>适合人群：{target_reader}</p>"
    ),
    "default": (
        "<p>{hook}</p>"
        "<p>本书以 {topic} 为核心，帮助读者建立扎实的统计思维，"
        "并能运用 Stata 独立完成完整的实证分析。</p>"
        "<p><b>本书特色：</b>{differentiator}</p>"
        "<p><b>适合人群：</b>{target_reader}</p>"
    ),
}


# ── 关键词生成 ───────────────────────────────────────────────────────

def generate_keywords(title: str, description: str, book_type: str = "stats-textbook") -> list:
    """
    根据书籍内容生成最多 7 个 KDP 关键词。
    """
    title_lower = title.lower()
    desc_lower = description.lower()

    keywords = []
    seen = set()

    def add(keyword: str):
        kw = keyword.strip()
        kw_lower = kw.lower()
        if kw and kw_lower not in seen and len(keywords) < MAX_KEYWORDS:
            # 跳过书名中已出现的词
            if kw_lower not in title_lower:
                keywords.append(kw)
                seen.add(kw_lower)

    # 按主题匹配
    topic_map = {
        "回归": "回归分析",
        "面板": "面板数据",
        "Stata": "Stata 教程",
        "统计": "统计学",
        "计量": "计量经济学",
        "商务数据": "商务数据分析",
        "教学": "统计学教学",
        "教材": "统计学教材",
        "科普": "统计科普",
    }
    for key, kw in topic_map.items():
        if key in title or key in desc_lower:
            add(kw)

    # 按书型添加
    if book_type == "stats-textbook":
        add("统计学教材")
        add("Stata 实操")
        add("经管统计")
    else:
        add("统计思维")
        add("经管科普")
        add("数据分析入门")

    add("回归分析")
    add("数据分析")

    if "经管" in title or "经管" in desc_lower:
        add("经管类教材")

    # 用关键词池补足
    pool = COMMON_KEYWORDS.get(book_type, COMMON_KEYWORDS["stats_textbook"]).split(", ")
    for kw in pool:
        add(kw)

    return keywords[:MAX_KEYWORDS]


# ── 描述生成 ───────────────────────────────────────────────────────

def generate_description(
    title: str,
    topic: str,
    target_reader: str,
    book_type: str = "stats-textbook",
    hook: str = "",
    differentiator: str = "",
) -> str:
    """生成 KDP 合规的 HTML 描述。"""
    book_type_key = book_type
    template = DESCRIPTION_TEMPLATES.get(book_type_key, DESCRIPTION_TEMPLATES["default"])

    if not hook:
        hook_map = {
            "回归": "你花了整整一个周末跑出来的回归结果，t 值显著，"
                     "R² 也不错——但你真的敢把这个表放进论文吗？",
            "统计": "每次看到论文里的回归表，你都觉得自己在猜谜。"
                       "系数符号对不对？标准误用对了没有？这本书就是来帮你把这些疑问都变成确定性的。",
            "Stata": "你安装了 Stata，跟着教程敲了一遍 do 文件，"
                      "结果出来了——然后呢？这本书教你从「跑出结果」到「读懂结果」。",
        }
        for key, h in hook_map.items():
            if key in title or key in topic:
                hook = h
                break
        if not hook:
            hook = f"如果你正在为 {topic} 头疼，这本书就是为你写的。"

    if not differentiator:
        if book_type == "stats-textbook":
            differentiator = "每章例题均提供完整 Stata do 文件，数据来自公开数据库，可直接复现；关键术语附英文原文，方便学术写作时对照使用。"
        else:
            differentiator = "不背公式，用真实商业场景建立统计直觉；每个概念都配有「一句话记住」小结，读完就能用。"

    text = template.format(
        topic=topic,
        target_reader=target_reader,
        hook=hook,
        differentiator=differentiator,
    )
    return text


# ── 校验 ──────────────────────────────────────────────────────────

def validate_metadata(title: str, subtitle: str, description: str, keywords: list) -> dict:
    """对照 KDP 规则校验元数据，返回校验结果字典。"""
    errors = []

    # 书名校验
    if re.search(r"\b畅销\b", title):
        errors.append("书名包含违禁促销词「畅销」")
    if re.search(r"\b免费\b", title):
        errors.append("书名包含违禁促销词「免费」")
    if re.search(r"\b新书\b", title):
        errors.append("书名包含违禁促销词「新书」")

    combined = (title + " " + subtitle).strip()
    if len(combined) > TITLE_SUBTITLE_MAX:
        errors.append(f"书名+副标题 = {len(combined)} 字符（上限：{TITLE_SUBTITLE_MAX}）")

    desc_len = len(description)
    if desc_len > MAX_DESCRIPTION_CHARS:
        errors.append(f"描述 = {desc_len} 字符（上限：{MAX_DESCRIPTION_CHARS}）")
    if desc_len < 100:
        errors.append(f"描述过短（{desc_len} 字符）— 建议 800–1000 字符以提高曝光度")

    # Emoji 检测
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", re.UNICODE
    )
    if emoji_pattern.search(description):
        errors.append("描述中包含 Emoji — KDP 不允许")

    if re.search(r"https?://|www\.|\.com|\.org|@", description):
        errors.append("描述中包含 URL 或邮箱 — KDP 不允许")

    if len(keywords) > MAX_KEYWORDS:
        errors.append(f"关键词过多（{len(keywords)} 个，上限：{MAX_KEYWORDS}）")
    if len(keywords) == 0:
        errors.append("未提供关键词 — 建议添加最多 7 个关键词")

    for kw in keywords:
        if '"' in kw or "'" in kw:
            errors.append(f"关键词包含引号：{kw}")
        if kw in ["书", "教材", "统计学"]:
            errors.append(f"过于通用的关键词：{kw}")

    return {
        "title_valid": not any("书名" in e for e in errors),
        "subtitle_length_ok": len(combined) <= TITLE_SUBTITLE_MAX,
        "description_length_ok": 100 <= desc_len <= MAX_DESCRIPTION_CHARS,
        "no_emoji": not bool(emoji_pattern.search(description)),
        "no_urls": not bool(re.search(r"https?://|www\.|\.com|\.org|@", description)),
        "keyword_count_ok": len(keywords) <= MAX_KEYWORDS,
        "description_char_count": desc_len,
        "errors": errors,
    }


# ── 主生成逻辑 ────────────────────────────────────────────────────────

def find_config(project_dir=None) -> str | None:
    """在常见位置查找 book-config.json。"""
    candidates = []

    if project_dir:
        p = Path(project_dir).expanduser().resolve() / "book-config.json"
        if p.exists():
            candidates.append(str(p))

    p = Path.cwd() / "book-config.json"
    if p.exists():
        candidates.append(str(p))

    for parent in [Path.cwd()] + list(Path.cwd().parents):
        wbp = parent / ".workbuddy" / "book-projects"
        if wbp.exists():
            for sub in sorted(wbp.iterdir()):
                cfg = sub / "book-config.json"
                if cfg.exists():
                    candidates.append(str(cfg))
            break

    script_dir = Path(__file__).resolve().parent.parent
    p = script_dir / "book-config.json"
    if p.exists():
        candidates.append(str(p))

    return candidates[0] if candidates else None


def load_book_config(config_path: str) -> dict:
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def generate_kdp_metadata(config: dict) -> dict:
    title = config.get("title", "")
    subtitle = config.get("subtitle", "")
    author = config.get("author", "作者")
    description_plain = config.get("description", "")
    target_reader = config.get("target_audience", "经管类专业学生")
    topic = config.get("topic", title)
    book_type = config.get("book_type", "stats-textbook")
    hook = config.get("hook", "")
    differentiator = config.get("differentiator", "")
    kdp_select = config.get("kdp_select", False)
    publisher = config.get("publisher", "")

    if not hook:
        hook_map = {
            "回归": "你花了整整一个周末跑出来的回归结果，t 值显著，R² 也不错——但你真的敢把这个表放进论文吗？",
            "统计": "每次看到论文里的回归表，你都觉得自己在猜谜。这本书帮你把所有疑问变成确定性。",
            "Stata": "你安装了 Stata，跟着教程敲了一遍 do 文件，结果出来了——然后呢？这本书教你从「跑出结果」到「读懂结果」。",
        }
        for key, h in hook_map.items():
            if key in title or key in topic:
                hook = h
                break

    html_description = generate_description(
        title=title,
        topic=topic,
        target_reader=target_reader,
        book_type=book_type,
        hook=hook,
        differentiator=differentiator,
    )

    keywords = generate_keywords(
        title=title,
        description=html_description,
        book_type=book_type,
    )

    validation = validate_metadata(title, subtitle, html_description, keywords)

    return {
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "description": {
            "html": html_description,
            "plain": description_plain,
            "char_count": validation["description_char_count"],
        },
        "keywords": keywords,
        "categories": config.get("categories", []),
        "language": config.get("language", "zh-CN"),
        "primary_audience": target_reader,
        "publisher": publisher,
        "isbn": None,
        "rights": "owned",
        "kdp_select": kdp_select,
        "book_type": book_type,
        "validation": validation,
        "_generated_by": "generate-kdp-metadata.py",
        "_config_source": "book-config.json",
    }


def main():
    parser = argparse.ArgumentParser(description="中文经管统计类书籍 — KDP 元数据生成器")
    parser.add_argument("--config", default=None, help="book-config.json 的路径")
    parser.add_argument("--project", default=None, help="包含 book-config.json 的项目目录")
    parser.add_argument("--interactive", action="store_true", help="交互模式：逐项修改元数据")
    args = parser.parse_args()

    config_path = args.config
    if not config_path:
        config_path = find_config(project_dir=args.project)
        if not config_path:
            print("错误：未找到 book-config.json。")
            print("  搜索路径：./book-config.json、.workbuddy/book-projects/*/book-config.json")
            print("\n  请先运行 setup-book.py 创建书籍项目。")
            sys.exit(1)
    print(f"使用配置文件：{config_path}")

    config = load_book_config(config_path)
    project_dir = Path(config_path).parent.resolve()

    kdp = generate_kdp_metadata(config)

    if args.interactive:
        print("\n📋 KDP 元数据 — 交互编辑器")
        print("=" * 50)

        print(f"\n1. 书名 [{len(kdp['title'])} 字符]：\n   {kdp['title']}")
        new_title = input("   回车保留，输入修改：").strip()
        if new_title:
            kdp["title"] = new_title

        print(f"\n2. 副标题 [{len(kdp.get('subtitle', ''))} 字符]：\n   {kdp.get('subtitle', '')}")
        new_sub = input("   回车保留，输入修改：").strip()
        if new_sub != "":
            kdp["subtitle"] = new_sub

        print(f"\n3. 作者：\n   {kdp['author']}")
        new_author = input("   回车保留，输入修改：").strip()
        if new_author:
            kdp["author"] = new_author

        print(f"\n4. 关键词（当前 {len(kdp['keywords'])}/7 个）：")
        for i, kw in enumerate(kdp["keywords"], 1):
            print(f"   {i}. {kw}")
        print("   回车保留当前列表，或逐行输入新关键词（空行结束）")
        kw_input = []
        while len(kw_input) < MAX_KEYWORDS:
            kw = input(f"   关键词 {len(kw_input)+1}（回车结束）：").strip()
            if not kw:
                break
            kw_input.append(kw)
        if kw_input:
            kdp["keywords"] = kw_input

        print(f"\n5. 描述（当前 {kdp['description']['char_count']} 字符）：")
        print("   " + kdp["description"]["html"][:200].replace("\n", " ") + "...")
        _ = input("   回车继续（详细描述请在 kdp-metadata.json 中手动编辑）：")

        kdp["validation"] = validate_metadata(
            kdp["title"], kdp.get("subtitle", ""),
            kdp["description"]["html"], kdp["keywords"]
        )

    output_path = project_dir / "kdp-metadata.json"
    output_path.write_text(
        json.dumps(kdp, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    print(f"\n✅ 已生成：{output_path}")

    v = kdp["validation"]
    print(f"\n📊 校验结果（{len(v['errors'])} 个问题）：")
    if v["errors"]:
        for err in v["errors"]:
            print(f"  ⚠  {err}")
    else:
        print("  ✅ 所有校验通过！")

    print(f"\n📋 KDP 元数据摘要：")
    print(f"  书名：    {kdp['title']}")
    if kdp.get("subtitle"):
        print(f"  副标题： {kdp['subtitle']}")
    print(f"  作者：    {kdp['author']}")
    print(f"  描述：    {v['description_char_count']} 字符")
    print(f"  关键词：  {', '.join(kdp['keywords'])}")
    print(f"  KDP Select：{'是（独家）' if kdp['kdp_select'] else '否（非独家）'}")

    print(f"\n下一步：")
    print(f"  1. 检查 kdp-metadata.json 中的描述内容")
    print(f"  2. 将描述 HTML 复制到 KDP 书籍描述字段")
    print(f"  3. 逐条输入 7 个关键词（每个填入一个输入框）")
    print(f"  4. 运行 merge-book.py 生成 HTML/PDF：")
    print(f"     python \"{Path(__file__).resolve()}\" --project \"{project_dir}\"")


if __name__ == "__main__":
    main()
