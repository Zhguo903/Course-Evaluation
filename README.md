# CourseInsight · 多伦多大学快速找课

帮助多伦多大学学生通过 **校区、课程 Level、Department / 学科和 BR / Distribution** 快速找到符合需求的课程，查看先修与修读要求，并核对已发布课表中的开课状态。

**课程目录与课表使用真实官方数据。** 默认展示三个官方本科目录的全部 **10,037 门课程**：St. George Faculty of Arts & Science 5,368 门、UTM 2,491 门、UTSC 2,178 门。另从官方 Timetable Builder 获取 **7,093 条开课记录**，覆盖 Fall 2026、Winter 2027 和 2026–2027 全年课程。数据核验日期为 **2026-10-13（多伦多时间）**。

项目的选课需求来自学生会、校友及课友群中常见的交流场景；当前课程事实均取自官方来源，每条课程保留来源链接。仓库不包含群聊摘录或生成的学生评价，v3 已移除模拟评分、教师和评论；v3.1 加入有来源标注的历史问卷数值与公开个人评价，v3.2 扩充公开课程资料与 Engineering 历史报告，不生成难度、工作量或 GPA 预测。

## 快速开始

```bash
git clone https://github.com/Zhguo903/Course-Evaluation.git
cd Course-Evaluation
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_pipeline.py
streamlit run app/streamlit_app.py
```

日常构建和页面启动使用仓库内已经核验的快照，无需网络。发布页提供源代码、课程 CSV 和可直接查询的 DuckDB 数据库：[下载版本](https://github.com/Zhguo903/Course-Evaluation/releases)。

## 页面功能

- 按校区、课程级别、官方学科分组和各校区分类筛选，默认展示全部目录课程。
- 搜索课程代码、名称和修读要求，优先显示精确课程代码与课程名称匹配。
- 选择已发布学期，查看“已发布开课”“已取消”“已发布课表中未找到”或“尚未核实”。
- 查看先修、共修、排除课程、建议准备、注册限制、来源链接和核验时间。
- 对比课程、分页查看结果，并下载当前筛选结果的 CSV。
- 在“学生评价与学习资料”页查看个人评价、历史问卷报告和学习资料；按“有已导入评价”或“有课程专属资料”筛选。
- 按资料类型及标题筛选；每课展示最多 20 条，完整索引可下载 CSV；展开数据覆盖查看各校区课程数。

“推荐”指根据用户条件筛选并解释匹配原因。课程顺序不代表教学质量、容易程度或个人注册资格。

## 数据来源与范围

| 数据 | 当前主来源 | 用途 |
| --- | --- | --- |
| St. George Arts & Science 本科目录 | [官方 Calendar](https://artsci.calendar.utoronto.ca/search-courses) | 课程代码、名称、学科、BR 与修读要求 |
| UTM 本科目录 | [官方 Calendar](https://utm.calendar.utoronto.ca/course-search) | 课程信息、Distribution 与修读要求 |
| UTSC 本科目录 | [官方 Calendar](https://utsc.calendar.utoronto.ca/search-courses) | 课程信息、Breadth 与修读要求 |
| 三校区已发布开课记录 | [官方 Timetable Builder](https://ttb.utoronto.ca/) | 学期、开课与取消状态、来源记录 |

“全部”指上述三个官方本科目录的完整课程集合，**不包含其他 St. George 专业学院或研究生课程**。目录校区表示所属目录，异地项目课程的实际教学地点应查看官方页面。

三个校区的分类保持独立：St. George Arts & Science 使用 BR 1–5；UTM 使用 Science / Humanities / Social Science 的 Distribution；UTSC 使用其五类 Breadth。不能把 UTM / UTSC 的类别强行套成 St. George BR 编号。

学科筛选取自官方学科章节，10,015 门已映射到官方章节，22 门未匹配的课程明确使用代码前缀分组；它不是所有课程的行政院系认定。53 门非标准课程的学分尚不能可靠确定，保留为空。

开课记录按课程与学期记录计数，与目录课程数不同。目录中 5,940 门在快照覆盖的学期至少有一条未取消的开课记录，106 门仅有取消记录，3,991 门未在完整课表中检索到。后者不表示课程今后不再开设；已发布开课也不表示有空位。快照会随官方调整而过时。

完整课程介绍通过官方链接阅读；仓库保留筛选所需元数据和条件类要求。官方空白字段显示“未列出”，不会自动解释成“无先修要求”。

详见 [数据口径](docs/data_sources.md)、[全网数据源调研](docs/data_source_research.md) 和 [课表接口与校验](docs/timetable_sources.md)。

## 学生评价与学习资料 · v3.2

新增三类可追溯内容，分别保存，不混成一个评分：

| 类型 | 已导入内容 | 如何理解 |
| --- | --- | --- |
| 历史问卷报告 | **70,453 条**三校区及 Engineering 历史报告，其中 **54,196 条**精确匹配当前目录的 **6,505 门课程** | 公开社区整理的历史官方问卷数值副本，年份因校区而异（2012–2024），未逐条与登录后的校方报告复核 |
| 公开个人评价 | **28 条**，来自同一位 CS ’25 作者的 2020–2025 课程回顾 | 中文转述、原帖链接和作者的 1–10 个人推荐分；没有核验作者选课身份，不代表学生共识 |
| 学习资源 | **752 条**，其中 746 条精确关联 **575 门**当前课程，另 6 条通用或历史入口 | 672 份大纲、18 条讲义、4 条练习、3 条模拟试卷、8 份旧试卷及课程网站、学生指南等；共有 748 个唯一 URL |

历史问卷分别展示整体学习体验、工作量、推荐意愿的 **1–5 原量表**。工作量高分表示负担更重，不能改名为课程难度。缺失保持为空，保留源异常；不跨学期、题目或教师报告计算综合分，也不将回复数加总当作独立学生人数。16,257 条无法精确匹配当前代码的历史报告保留在数据库，不错误关联到相似课程。

Engineering 源新增 14 门课程的历史评价覆盖，未找到已核验的 2025–2026 新原始问卷；新版本不会用旧报告冒充当前评价。

原始历史文件来自公开 [数据帖](https://www.reddit.com/r/UofT/comments/1ihe5tu/) 中贡献者分享的 [三校区及 Engineering CSV 文件夹](https://drive.google.com/drive/folders/1Pg7qk7N2PvKaqMsGjw09El9jsWVmHPEB)。仅保留数值事实与来源，不镜像原 CSV 全文、教师名单或受限评价。详细字段、异常及来源性质见 [历史评价说明](docs/feedback_data_sources.md)。

公开个人评价来自 [作者原帖](https://www.reddit.com/r/UofT/comments/1kjq8ji/rating_and_reviewing_every_course_i_took_at_uoft/)。历史 MAT137、MAT235 因代码缺失或变更未自动匹配到当前课程。

[官方评价入口](https://teaching.utoronto.ca/course-evaluations/for-students/) 仍需 UTORid；[UofT Index](https://uoftindex.com/) 仅作为外部查询入口，未抓取其数据库。资料只保存链接与元数据；需要登录的往年试卷入口会明确标注，未复制试卷或教材全文。

发布页另提供完整历史评价 CSV、个人评价 CSV、资料索引 CSV 和含 **10 张表**的 DuckDB。详见 [最新覆盖统计](docs/data_coverage.md) 与 [学习资料来源和重建](docs/learning_resources.md)。

## 更新官方数据

```bash
python scripts/update_catalog.py
python scripts/update_timetable.py
python run_pipeline.py
```

更新脚本会显式访问官方站点。目录通过完整导出、搜索分页总数和首尾顺序核对覆盖范围；课表通过完整响应与官方分页总数交叉核验。哈希、来源、时间、校区及学期数量写入对应 manifest。下载或校验失败会中止，避免把部分结果发布为完整数据。

流水线先校验，再构建临时数据库并原子替换已发布文件；失败保留原数据库。运行页面不会触发自动抓取。

历史评价可显式刷新，资料与个人评价由人工核验后维护：

```bash
python scripts/import_evaluations.py --fetch
python scripts/verify_support.py
python run_pipeline.py
```

资料批次扩展与去重命令见 [学习资料维护](docs/learning_resources.md)。修改已核验的个人评价或资料索引后，使用 `python scripts/verify_support.py --refresh-manifest` 更新元数据哈希，再重建数据库。历史评价也支持 `--source-dir` 离线重放；源网址失效、解析或校验失败时不会用生成内容替代。


## 数据结构

```text
data/reference/uoft_courses.json          官方课程元数据
data/reference/catalog_manifest.json     目录来源、完整性与哈希
data/reference/timetable_offerings.json  官方开课记录
data/reference/timetable_manifest.json   课表来源、覆盖范围与哈希
data/reference/course_evaluations.json   历史问卷数值及评价 manifest
data/reference/student_reviews.json     有来源的个人意见与原始尺度
data/reference/course_resources.json    资料链接与访问条件
data/reference/feedback_sources.json    评价来源及接入状态
data/reference/support_manifest.json    评价／资料元数据哈希
data/warehouse/course_insight.duckdb     本地生成的查询数据库
src/catalog.py                           官方目录解析与校验
src/timetable.py                         开课获取、校验与状态标注
src/finder.py                            条件筛选、搜索与匹配理由
src/warehouse.py                         原子发布 DuckDB
app/streamlit_app.py                     找课与对比页面
```

数据库含课程目录、开课记录、找课结果、学期覆盖、质量报告、来源清单、个人评价、历史评价、资料和评价来源登记十张表。字段见 [数据字典](docs/data_dictionary.md)，查询示例见 [SQL](sql/course_finder_queries.sql)，匹配规则见 [说明](docs/matching_rules.md)。

## 开发验证

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
python run_pipeline.py
```

测试覆盖完整目录解析、官方字段与分类、课表哈希和覆盖校验、全年课程学期归属、未知状态、条件筛选、数据库原子发布以及页面交互。GitHub Actions 使用 Python 3.11 和 3.13 验证。

## English overview

CourseInsight helps University of Toronto students find courses by campus, level, academic subject and campus-specific breadth or distribution category. Version 3 uses complete official undergraduate catalogues for St. George Arts & Science, UTM and UTSC: 10,037 courses, supplemented by 7,093 official timetable records retrieved on October 13, 2026. The interface provides transparent matching reasons, published offering status, original requirement text, comparison, CSV export and official source links. Missing or unpublished information remains explicitly unknown. There are no synthetic reviews or inferred difficulty, workload or GPA scores.

Version 3.2 includes 70,453 historical survey reports from publicly shared third-party copies (54,196 reports matching 6,505 current courses), 28 attributed individual opinions from one author, and 752 resource entries covering 575 current courses through 748 unique URLs. Materials include 672 syllabi, 18 lecture-note links, 4 practice links, 3 practice exams and 8 past exams, plus course sites and student guides. Historical survey values retain their original question meanings and 1–5 scales; individual recommendation ratings retain their 1–10 scale. Reports are never combined into a universal score, and response counts are not presented as unique students. Unmatched historical course codes remain unassigned. Resource content and restricted materials are not mirrored.
