# CourseInsight · 多伦多大学快速找课

帮助多伦多大学学生通过 **校区、课程 Level、Department / 学科和 BR / Distribution** 快速找到符合需求的课程，查看先修与修读要求，并核对已发布课表中的开课状态。

**v3 使用真实官方数据。** 默认展示三个官方本科目录的全部 **10,037 门课程**：St. George Faculty of Arts & Science 5,368 门、UTM 2,491 门、UTSC 2,178 门。另从官方 Timetable Builder 获取 **7,093 条开课记录**，覆盖 Fall 2026、Winter 2027 和 2026–2027 全年课程。数据核验日期为 **2026-10-13（多伦多时间）**。

项目的选课需求来自学生会、校友及课友群中常见的交流场景；当前课程事实均取自官方来源，每条课程保留来源链接。仓库不包含群聊摘录或生成的学生评价，v3 已移除模拟评分、教师、评论、难度、工作量和 GPA 预测。

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

## 更新官方数据

```bash
python scripts/update_catalog.py
python scripts/update_timetable.py
python run_pipeline.py
```

更新脚本会显式访问官方站点。目录通过完整导出、搜索分页总数和首尾顺序核对覆盖范围；课表通过完整响应与官方分页总数交叉核验。哈希、来源、时间、校区及学期数量写入对应 manifest。下载或校验失败会中止，避免把部分结果发布为完整数据。

流水线先校验，再构建临时数据库并原子替换已发布文件；失败保留原数据库。运行页面不会触发自动抓取。

## 数据结构

```text
data/reference/uoft_courses.json          官方课程元数据
data/reference/catalog_manifest.json     目录来源、完整性与哈希
data/reference/timetable_offerings.json  官方开课记录
data/reference/timetable_manifest.json   课表来源、覆盖范围与哈希
data/warehouse/course_insight.duckdb      本地生成的查询数据库
src/catalog.py                           官方目录解析与校验
src/timetable.py                         开课获取、校验与状态标注
src/finder.py                            条件筛选、搜索与匹配理由
src/warehouse.py                         原子发布 DuckDB
app/streamlit_app.py                     找课与对比页面
```

数据库含课程目录、开课记录、找课结果、学期覆盖、质量报告和来源清单六张表。字段见 [数据字典](docs/data_dictionary.md)，查询示例见 [SQL](sql/course_finder_queries.sql)，匹配规则见 [说明](docs/matching_rules.md)。

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
