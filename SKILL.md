---
name: Statistics-book-writer
description: >
  面向中文经管类统计学书籍的 AI 写作工作流：选题 → 大纲 → 多轮交互式章节写作 →
  封面设计 → 格式化 HTML/PDF。支持两种书型：经管类统计学教材、
  经管类统计学科普读物。写作环节通过多轮对话收集用户素材与要求，
  逐章反馈写作建议后再落笔。需用 Python 3 运行配套脚本，
  可选 Playwright 生成 PDF。
agent_created: true
---

# 中文经管统计类书籍写作 Skill

完整 AI 驱动工作流：**选题 → 大纲 → 多轮交互式章节写作 → 封面设计 → 格式化输出**。

支持两种书型：
- **经管类统计学教材**：面向高校师生，结构严谨，含例题、习题、知识框
- **经管类统计学科普读物**：面向职场人士/普通读者，通俗易懂，案例驱动

---

## 触发条件

用户说出以下任意表达时触发本 skill：
- "写书 / 新建书籍项目 / 开始写一本…"
- "统计学教材 / 统计科普 / 经管统计"
- "帮我写第一章 / 写第 X 章"
- "生成书籍大纲 / 合并章节 / 导出 PDF 书"
- "设计封面 / 生成 KDP 元数据"（如涉及出版）

---

## 核心原则

1. **中文书稿**：全书用中文写作，术语准确，例句贴合中国经管场景
2. **多轮交互写作**：Phase 4 每章写作前，先与用户对话收集素材和要求，再动笔
3. **两种书型风格严格区分**：教材偏严谨规范，科普偏生动易懂
4. **只依赖文件系统和 Python 3**：无平台特定依赖

---

## 项目目录结构

```
{project_path}/
├── book-config.json      ← 书籍配置（Phase 1 生成）
├── outline.md            ← 内容大纲（Phase 2 生成）
├── kdp-metadata.json     ← 出版元数据（Phase 3 生成，可选）
├── chapters/             ← 所有章节 .md 文件（Phase 4 生成）
│   ├── ch01-intro.md
│   ├── ch02-body.md
│   └── ...
├── cover.jpg             ← 封面图（Phase 4.5 生成，可选）
└── Book-Output/          ← 最终输出（Phase 5 生成）
    ├── {slug}.html       ← 完整 HTML 书籍
    └── {slug}.pdf        ← 打印级 PDF（需 Playwright）
```

> ⚠️ 原始章节文件**永不删除**，`chapters/` 中的文件始终保留，方便日后编辑或重新合并。

---

## 五阶段工作流

---

### Phase 1：选题与项目初始化

**目标**：确认书籍创意，创建项目目录和配置文件。

#### Step 1.1 — 收集书籍信息

向用户询问以下内容（可参考已有项目列表 `book-writing-projects.md`，如有）：

| 字段 | 必填 | 说明 | 示例 |
|-------|--------|------|------|
| 书名 | ✅ | 工作书名，可后续调整 | 《商务数据统计分析》 |
| 副标题 | ❌ | 补充说明 | 基于 Stata 的经管实证方法 |
| 作者名 | ✅ | 可用笔名 | 胡久凯 |
| 目标读者 | ✅ | 谁读这本书 | 经管类本科生 / 职场数据分析师 |
| 核心主题/问题 | ✅ | 这本书解决什么问题 | 让经管学生掌握用 Stata 做回归分析 |
| **书型** | ✅ | 二选一，见下方说明 | `stats-textbook` 或 `stats-popular` |
| 出版社名 | ❌ | KDP 出版时填写 | — |
| KDP Select | ❌ | 亚马逊独家（默认 false） | — |

**书型说明：**

| 书型值 | 名称 | 特点 |
|----------|------|------|
| `stats-textbook` | 经管类统计学教材 | 章节结构固定：引言→正文→小结→习题；语言规范；含知识框、例题、Stata 代码 |
| `stats-popular` | 经管类统计学科普读物 | 章节结构灵活：场景引入→核心概念→案例→行动建议；语言生动；多用比喻和真实商业案例 |

#### Step 1.2 — 生成项目 slug

将书名转为 URL 安全字符串：
```
《商务数据统计分析——基于 Stata》
→ "shangwu-shuju-tongji-fenxi"
```

#### Step 1.3 — 初始化项目

运行初始化脚本：
```bash
python "{skill_dir}/scripts/setup-book.py" --book {slug}
```

或手动创建：
1. 创建 `{project_path}/chapters/` 目录
2. 创建 `{project_path}/Book-Output/` 目录
3. 创建 `book-config.json`（格式见下）
4. 创建 `outline.md` 并填入章节标题

#### `book-config.json` 输出格式

```json
{
  "workspace": ".",
  "chapters_dir": "chapters",
  "output_dir": "Book-Output",
  "cover_image": "",
  "chapters": [
    "ch01-introduction.md",
    "ch02-descriptive-stats.md",
    "ch03-regression.md",
    "appendix.md"
  ],
  "title": "商务数据统计分析",
  "subtitle": "基于 Stata 的经管实证方法",
  "author": "胡久凯",
  "topic": "让经管学生掌握用 Stata 做回归分析",
  "target_audience": "经管类本科生、研究生",
  "book_type": "stats-textbook",
  "description": "一本面向经管学生的 Stata 统计实务教材",
  "publisher": "",
  "kdp_select": false,
  "categories": [],
  "toc_items": [
    "第一章 导论",
    "第二章 描述性统计",
    "第三章 回归分析",
    "附录"
  ],
  "slug": "shangwu-shuju-tongji-fenxi",
  "language": "zh-CN"
}
```

---

### Phase 2：内容大纲

**目标**：在正式写作前规划完整的章节结构。

**先读取参考文件**：`references/writing-style.md`，了解两种书型的章节结构规范。

创建 `outline.md`，格式如下：

```markdown
# {书名} — 内容大纲

**副标题：** {subtitle}
**作者：** {author}
**目标读者：** {target_audience}
**字数目标：** 80,000–120,000 字（8–10 章 + 附录）

## 第一章：{标题}
- 核心知识点 1
- 核心知识点 2
- 核心知识点 3
- **目标字数：** 3,000–5,000 字

## 第二章：{标题}
...

## 附录：习题答案与延伸阅读
- 习题解答
- 推荐阅读文献
- **目标字数：** 2,000–3,000 字
```

**需要与用户确认的关键决策：**
- 总章数（建议 8–10 章 + 附录）
- 章节顺序与逻辑递进关系
- 是否包含附录

---

### Phase 3：KDP 元数据生成（可选）

**目标**：如计划出版到亚马逊，在完稿前生成出版所需的元数据。

**先读取参考文件**：`references/kdp-metadata.md`，了解 KDP 字段规范。

运行生成脚本：
```bash
python "{skill_dir}/scripts/generate-kdp-metadata.py" --project "{project_path}"
```

交互模式（可逐项修改）：
```bash
python "{skill_dir}/scripts/generate-kdp-metadata.py" --project "{project_path}" --interactive
```

生成文件：`kdp-metadata.json`，包含书名、副标题、作者、HTML 描述（≤4,000 字符）、7 个关键词、校验结果。

> 中文书籍如不在亚马逊出版，可跳过此阶段。

---

### Phase 4：章节写作（核心改动）

**目标**：逐章写作，每章写作前通过**多轮对话**收集用户素材与要求。

**先读取参考文件**：`references/writing-style.md`，严格按照对应书型的风格要求写作。

#### 工作流程（每章循环）

**第一步：发起对话，收集素材**

对当前章节，向用户发送如下提示并等待回复：

```
📝 即将写作：【第一章：导论】

请提供以下素材和要求（有多少提供多少，没有可跳过）：
1. 这一章你想覆盖的核心知识点有哪些？
2. 有没有特定的案例、数据集或 Stata 代码片段要用到？
3. 有没有必须引用的文献或理论？
4. 对这一章的写作有什么特殊要求（深度、篇幅、侧重等）？
5. 有没有需要避免的内容？

请把素材直接发给我，我们来讨论。
```

**第二步：分析素材，反馈写作建议**

收到用户素材后，回复如下内容：

```
收到！我整理了这一章的写作建议：

**章节：** 第一章：导论
**建议结构：**
- 1.1 引例（用 XXX 案例引入）
- 1.2 统计学在经管研究中的角色（结合你提供的文献）
- 1.3 本书的使用方法（Stata 版本、数据来源）
- 1.4 本章小结

**需要你补充的素材：**
- [ ] 引例的具体数据或背景（目前只有概念描述）
- [ ] 你希望用哪个 Stata 命令作为第一个例子？

**我的写作计划：**
语言风格取「教材型」：规范、简洁，用「例 X-X」编号，
关键术语首次出现时加粗并附英文原文。

确认没问题的话，我开始写作；
有需要调整的地方请告诉我。
```

**第三步：用户确认后，正式写作**

用户回复确认（或提出修改意见，回到第二步）后，按 `writing-style.md` 的规范写作并保存到 `chapters/chXX-{slug}.md`，然后更新 `book-config.json` 中的 `chapters` 和 `toc_items`，并在 `outline.md` 中标记该章为已完成。

**第四步：章节完成，询问是否继续**

```
✅ 第一章已完成，保存至 chapters/ch01-daolun.md（约 3,200 字）

是否继续写作下一章（第二章：描述性统计）？
```

重复以上四步，直至所有章节完成。

#### 两种书型的章节结构模板

**教材型（`stats-textbook`）：**

```markdown
# 第一章 {章节标题}

## 引例
{用一个经管实证场景引入本章主题，1–2 段}

## {第一节标题}
{正文，350–500 字小节}

### 例 1-1 {例标题}
{Stata 代码 + 输出结果 + 解读，按「标题→描述段落→代码」格式}

## {第二节标题}
{正文}

## 本章小结
{3–5 条要点，每条 1–2 行}

## 习题
1. {计算/实操题，附数据来源说明}
2. ...
```

**科普型（`stats-popular`）：**

```markdown
# 第一章 {章节标题}

{开篇场景，2–3 段，直接切入读者痛点或好奇点}

## {核心概念，用口语化标题}
{正文，短段落，多举例，避免公式}

> **核心要点：** {一句话总结本节}

## {下一个概念}

**本章行动清单：**
1. {具体可操作的步骤}
2. ...
```

#### 字数目标

| 元素 | 教材型 | 科普型 |
|-------|----------|----------|
| 每章正文 | 3,000–5,000 字 | 2,000–3,500 字 |
| 本章小结/行动清单 | 200–300 字 | 150–250 字 |
| 附录 | 2,000–3,000 字 | 1,500–2,500 字 |

---

### Phase 4.5：封面设计（可选）

**目标**：根据大纲和书籍定位生成专业封面。

**先读取**：`outline.md` 和 `kdp-metadata.json`（如有），理解书籍主题、读者和基调。

#### Step 4.5.1 — 准备设计简报

从 `outline.md` 中提取：
- **书籍基调**：严谨学术 / 亲和易懂 / 实操导向？
- **目标读者**：年龄层、专业背景、使用场景
- **视觉隐喻**：什么图像最能代表核心主题？
- **色彩倾向**：冷色系（专业感）/ 暖色系（亲和力）？

#### Step 4.5.2 — 生成封面

使用图像生成工具，提示词如下：

```
你是非常资深的中文经管类书籍封面设计师。

书籍信息：
书名：{title}
副标题：{subtitle}
作者：{author}
目标读者：{target_audience}
书籍类型：{book_type}
核心主题：{topic}

设计要求：
1. 风格符合经管类书籍的学术/专业定位
2. 书名文字清晰易读（缩略图尺寸下可辨识）
3. 色彩搭配符合目标读者的审美
4. 如有 Stata/数据分析元素，可含蓄体现
5. 输出 JPG 格式

请直接生成封面图片。
```

将生成的图片保存为项目根目录下的 `cover.jpg`。

#### Step 4.5.3 — 更新 book-config.json

```json
{
  "cover_image": "cover.jpg"
}
```

> 注意：如用于正式出版，封面分辨率建议 ≥300 DPI，尺寸 ≥2500×2500 px。

---

### Phase 5：合并成书（HTML + PDF）

**目标**：将所有章节和封面合并为完整格式化书籍。

**Step 5.1 — 验证配置**

确认 `book-config.json` 包含：
- `chapters` 列表完整（文件名正确、顺序正确）
- `toc_items` 与章节一一对应
- `title`、`subtitle`、`author`、`description` 已填写

**Step 5.2 — 运行合并脚本**

```bash
python "{skill_dir}/scripts/merge-book.py" --project "{project_path}"
```

脚本执行以下操作：
1. 读取 `{project_path}/book-config.json`
2. 加载 `chapters/` 下所有 Markdown 章节文件
3. 将 Markdown 转为 HTML（支持表格、列表、代码块、引用）
4. 构建完整 HTML 文档：封面 → 描述 → 目录 → 章节 → 封底
5. 如已安装 Playwright，额外生成 A4 PDF

**Step 5.3 — 验证输出**

- 在浏览器中打开 `{project_path}/Book-Output/{slug}.html`，检查排版
- 如有 PDF，检查 `{project_path}/Book-Output/{slug}.pdf` 的分页效果

**输出文件：**

| 文件 | 位置 |
|------|------|
| 完整 HTML 书籍 | `{project_path}/Book-Output/{slug}.html` |
| 打印级 PDF | `{project_path}/Book-Output/{slug}.pdf` |
| 原始章节文件 | `{project_path}/chapters/*.md` ← **永不删除** |
| KDP 元数据 | `{project_path}/kdp-metadata.json` |

---

## 脚本参考

所有脚本位于 `{skill_dir}/scripts/`，仅需 Python 3 标准库
（`merge-book.py` 可选依赖 `playwright` 用于 PDF 生成）。

| 脚本 | 用途 | 关键用法 |
|--------|------|----------|
| `setup-book.py` | 新建书籍项目 | `python setup-book.py --book {slug}` |
| `generate-kdp-metadata.py` | 生成 KDP 出版元数据 | `python generate-kdp-metadata.py --project {path}` |
| `merge-book.py` | 合并章节 → HTML + PDF | `python merge-book.py --project {path}` |

### 配置文件自动发现

所有脚本按以下优先级自动查找 `book-config.json`：
1. `--config /path/to/config.json`（显式指定）
2. `--project /path/to/project/`（在项目目录中查找）
3. `./book-config.json`（当前工作目录）
4. `.workbuddy/book-projects/*/book-config.json`（常见模式）
5. 脚本所在目录（skill 级配置）

### PDF 生成（可选）

如未安装 `playwright`，`merge-book.py` 仍会生成 HTML。
启用 PDF 生成：
```bash
pip install playwright && playwright install chromium
```

---

## 写作风格快速对照

| 维度 | 教材型 `stats-textbook` | 科普型 `stats-popular` |
|-------|--------------------------|-----------------------|
| 语言 | 规范、简洁、学术化 | 生动、口语化、接地气 |
| 结构 | 固定：引例→正文→例题→小结→习题 | 灵活：场景→概念→案例→行动 |
| 代码 | 必需，完整 Stata 代码 + 输出 | 可选，示例为主，不要求复现 |
| 术语 | 首次出现加粗 + 英文原文 | 避免过多术语，必要时用比喻解释 |
| 例题编号 | `例 X-X` 统一格式 | 不强制编号 |
| 每章字数 | 3,000–5,000 | 2,000–3,500 |

> 详细规范见 `references/writing-style.md`。

---

## Skill 文件结构

```
Statistics-book-writer/
├── SKILL.md                          ← AI 智能体指令（本文件）
├── README.md                         ← 使用说明
├── scripts/
│   ├── setup-book.py                 ← Phase 1：项目初始化
│   ├── generate-kdp-metadata.py      ← Phase 3：KDP 元数据
│   └── merge-book.py                 ← Phase 5：HTML + PDF 生成
└── references/
    ├── kdp-metadata.md               ← 亚马逊 KDP 字段规范
    └── writing-style.md              ← 中文写作风格指南（教材型 + 科普型）
```

**工作流顺序**：Phase 1 → Phase 2 → Phase 3 → **Phase 4（多轮交互）** → Phase 4.5 → Phase 5
