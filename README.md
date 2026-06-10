# Statistics-book-writer（中文经管统计类书籍版）

**把你的经管统计书籍创意，用 AI 多轮对话的方式变成成稿。**

支持两种书型：
- **经管类统计学教材**（`stats-textbook`）：面向高校师生，结构严谨，含例题、习题、Stata 代码
- **经管类统计学科普读物**（`stats-popular`）：面向职场人士，通俗易懂，案例驱动

适用 AI 智能体：**WorkBuddy**、**Claude Code**、**Codex** 等任何有文件系统访问权限的智能体。无智能体特定依赖 —— 仅需 Python 3 + 可选的 Playwright。

---

## 功能概述

```
选题 → 大纲 → 多轮交互式章节写作 → 封面设计 → HTML + PDF 成书
```

| 阶段 | 说明 |
|-------|-------------|
| **1. 选题** | 确定书名、作者、目标读者、核心问题、书型 |
| **2. 大纲** | 规划章节结构（8–10 章 + 附录） |
| **3. KDP 元数据** |（可选）生成书名、副标题、HTML 描述、7 个关键词 |
| **4. 章节写作** | AI 逐章与用户对话收集素材，确认后落笔 |
| **5. 合并** | 将章节合并为格式化的 HTML + PDF 书籍 |

---

## 快速开始

### 1. 初始化书籍项目

```bash
python "{skill_dir}/scripts/setup-book.py"
```

按提示填写（中文输入）：
```
书名：商务数据统计分析
副标题：基于 Stata 的经管实证方法
作者：胡久凯
目标读者：经管类本科生、研究生
书型：[1] 经管类统计学教材  /  [2] 经管类统计学科普读物
```

生成以下内容：
- `book-config.json` — 项目配置
- `outline.md` — 章节大纲
- `chapters/` — 章节目录
- `chapters/ch01-xxx.md` — 第一章示例模板

---

### 2. 多轮交互式章节写作（核心改动）

AI 对每一章执行以下四步循环：

**第一步：AI 发起对话，收集素材**
> 📝 即将写作：【第一章：导论】
> 请提供素材：核心知识点、案例/数据集/Stata 代码片段、必须引用的文献、特殊写作要求……

**第二步：AI 分析素材，反馈写作建议**
> 收到！我整理了这一章的写作建议：
> **建议结构：** 1.1 引例 → 1.2 统计学在经管研究中的角色 → 1.3 本书使用方法 → 1.4 小结
> **需要你补充的素材：** 引例的具体数据或背景
> **我的写作计划：** 语言风格取「教材型」，例 X-X 编号，关键术语首次出现时加粗附英文原文。
> 确认没问题的话，我开始写作。

**第三步：用户确认后正式写作**
保存至 `chapters/chXX-xxx.md`，更新 `book-config.json` 和 `outline.md`。

**第四步：完成一章，询问是否继续**
> ✅ 第一章已完成（约 3,200 字）。是否继续写作下一章（第二章：描述性统计）？

---

### 3. 生成 KDP 元数据（可选，如出版到亚马逊）

```bash
python "{skill_dir}/scripts/generate-kdp-metadata.py" --project "./{slug}"
```

输出 `kdp-metadata.json`，包含：
- `title` / `subtitle` / `author`
- `description.html` — KDP 合规 HTML，≤4,000 字符
- `keywords[]` — 7 个 KDP 合规关键词
- `validation{}` — 字符计数、违禁内容校验

交互模式（逐项修改）：
```bash
python "{skill_dir}/scripts/generate-kdp-metadata.py" --project "./{slug}" --interactive
```

---

### 4. 合并为书籍（HTML + PDF）

```bash
python "{skill_dir}/scripts/merge-book.py" --project "./{slug}"
```

输出：
- `Book-Output/{slug}.html` — 完整格式化中文书籍（支持打印样式）
- `Book-Output/{slug}.pdf` — A4 PDF（需安装 Playwright）

---

## 项目结构

```
my-book/
├── book-config.json      ← 所有书籍元数据（编辑此文件管理章节）
├── outline.md            ← 章节规划大纲
├── kdp-metadata.json    ←（可选）KDP 出版元数据
├── chapters/             ← 所有章节 .md 文件（保留，不会被删除）
│   ├── ch01-daolun.md
│   ├── ch02-miaoshuxing-tongji.md
│   └── ...
├── cover.jpg             ←（可选）封面图片
└── Book-Output/          ← 仅最终输出文件
    ├── my-book.html
    └── my-book.pdf
```

---

## `book-config.json` 字段说明

```json
{
  "title": "商务数据统计分析",
  "subtitle": "基于 Stata 的经管实证方法",
  "author": "胡久凯",
  "topic": "让经管学生掌握用 Stata 做回归分析",
  "target_audience": "经管类本科生、研究生",
  "book_type": "stats-textbook",
  "description": "一本面向经管学生的 Stata 统计实务教材",
  "kdp_select": false,
  "publisher": "",
  "categories": [],
  "language": "zh-CN",
  "chapters": ["ch01-daolun.md", "ch02-miaoshuxing-tongji.md"],
  "toc_items": ["第一章 导论", "第二章 描述性统计"],
  "slug": "shangwu-shuju-tongji-fenxi"
}
```

| 字段 | 必填 | 说明 |
|-------|----------|-------|
| `title` | ✅ | 书名 |
| `subtitle` | ❌ | 书名 + 副标题合计 < 200 字符 |
| `author` | ✅ | 作者名（可用笔名） |
| `topic` | ✅ | 核心主题，用于描述生成 |
| `target_audience` | ✅ | 目标读者群体 |
| `book_type` | ✅ | `stats-textbook` 或 `stats-popular` |
| `chapters` | ✅ | 章节文件名，按阅读顺序排列 |
| `toc_items` | ✅ | 章节标题（与 chapters 一一对应） |
| `slug` | ✅ | URL 安全的项目标识符 |

---

## 两种书型的结构差异

### 教材型（`stats-textbook`）

```
# 第 X 章 {标题}

## 引例
{经管实证场景引入，150–250 字}

## 第 X.1 节标题
{正文 350–600 字}

### 例 X-X {例题标题}
**题目描述：** {背景}
**Stata 代码：**
```stata
...
```
**输出结果：** {Markdown 表格}
**结果解读：** {经管意义解释}

## 本章小结
● {要点1}
● {要点2}

## 习题
1. {计算/实操题，附数据来源}
```

### 科普型（`stats-popular`）

```
# 第 X 章 {口语化标题}

{开篇场景，2–3 段，直接切入读者痛点}

## {核心概念，大白话标题}
{解释，短段落，避免公式}

> **一句话记住：** {关键要点}

**本章行动清单：**
1. {具体可操作}
2. ...
```

---

## 写作风格快速对照

| 维度 | 教材型 `stats-textbook` | 科普型 `stats-popular` |
|-------|--------------------------|-----------------------|
| 语言 | 规范、严谨、精练 | 生动、口语化、接地气 |
| 结构 | 固定：引例→正文→例题→小结→习题 | 灵活：场景→概念→案例→行动 |
| 代码 | 必需，完整 Stata 代码 + 输出 | 可选，示例为主 |
| 术语 | 首次出现加粗 + 英文原文 | 避免过多术语，必要时用比喻 |
| 每章字数 | 3,000–5,000 | 2,000–3,500 |

> 详细规范见 `references/writing-style.md`。

---

## 依赖

| 依赖 | 是否必需 | 安装方式 |
|-----------|----------|---------|
| Python 3 | ✅ | `python --version`（3.8+） |
| `playwright` | ❌（仅 PDF 需要） | `pip install playwright && playwright install chromium` |

所有脚本基于 Python 3 标准库运行。`playwright` 仅用于 PDF 生成——HTML 不依赖它即可生成。

---

## 脚本说明

| 脚本 | 功能 |
|--------|-------------|
| `setup-book.py` | 交互式项目初始化（中文问答） |
| `generate-kdp-metadata.py` | 生成 KDP 出版元数据（中文模板） |
| `merge-book.py` | 合并章节 → 中文 HTML + PDF |

所有脚本支持配置文件自动发现：

```bash
# 方式 1：指定项目路径（推荐）
python merge-book.py --project "./my-book"

# 方式 2：指定配置文件路径
python merge-book.py --config "./my-book/book-config.json"

# 方式 3：自动发现
python merge-book.py
```

---

## 文件结构

```
Statistics-book-writer/
├── SKILL.md                         ← AI 智能体指令（核心文件）
├── README.md                        ← 使用说明（本文件）
├── scripts/
│   ├── setup-book.py                ← Phase 1：项目初始化
│   ├── generate-kdp-metadata.py     ← Phase 3：KDP 元数据
│   └── merge-book.py                ← Phase 5：HTML + PDF 生成
└── references/
    ├── kdp-metadata.md              ← 亚马逊 KDP 字段规范
    └── writing-style.md             ← 中文写作风格指南（教材型 + 科普型）
```

---

## 许可证

MIT

---

## 更新日志

### v2.0 — 2026-06（中文经管统计类定制版）
- **重构**：从英文畅销书工具改造为中文经管统计类书籍写作工具
- **新增**：两种书型 `stats-textbook` / `stats-popular`
- **新增**：Phase 4 多轮交互式章节写作流程（AI 先收集素材、反馈建议，确认后再写作）
- **重写**：`references/writing-style.md` 完整中文写作规范
- **更新**：所有脚本模板改为中文，`setup-book.py` 交互问答中文化
- **更新**：`merge-book.py` HTML 模板 `lang="zh-CN"`，中文字体栈

### v1.1 — 2026-05（原版）
- 原版英文畅销书工作流
