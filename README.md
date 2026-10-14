# CourseInsight · 多伦多大学课程探索与选课推荐

[![Verify CourseInsight](https://github.com/Zhguo903/Course-Evaluation/actions/workflows/ci.yml/badge.svg)](https://github.com/Zhguo903/Course-Evaluation/actions/workflows/ci.yml)

CourseInsight 面向多伦多大学学生，结合 **真实课程目录、校区广度/分布要求、先修条件与模拟选课反馈**，帮助学生更快比较感兴趣的课程，找到符合学习目标和课程要求的选择。项目串联 **数据清洗 → 分层数仓 → 课程画像 → 可解释推荐 → 交互式看板**。

根据项目维护者的说明，评价样本的内容设计参考了学生会、校友及课友群中常见的选课交流主题，包括课程工作量、考试难度、教学方式和实用性。公开版本使用按这些主题生成的模拟评价，**不是群聊原文，也不代表真实学生对具体课程或教师的评价**。本仓库未导入原始群聊记录。

**课程信息来源：** 课程名称、完整课程代码、学分、BR/Distribution 分类、先修及相关要求来自多伦多大学三个校区的官方 Academic Calendar，并保留每门课的来源链接与抓取日期。

**数据说明：** 课程元数据来自官方目录；教师、开课、评分和评论为模拟数据，未采集真实学生评价。GPA 友好度、职业相关性和推荐分是公开规则计算的辅助指标，不代表成绩预测、就业预测或已验证的推荐准确率。

## 快速开始

需要 Python 3.10+；GitHub Actions 在 Python 3.11 与 3.13 上运行检查。

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

浏览器打开终端中显示的本地地址（通常为 `http://localhost:8501`）。首次打开时若尚未生成数据，也可点击看板中的初始化按钮。

默认数据规模：**200 门官方目录课程（St. George 80、UTM 60、UTSC 60）**，配合 **60 位虚构教师、8 个模拟学期、800 条模拟开课记录、12,000 条模拟评论**。这是覆盖三个校区的选取样本，不是多伦多大学全部课程或当前学期开课清单。固定随机种子保证同一版本可复现。

## 能做什么

| 功能 | 使用方式与实现 |
| --- | --- |
| 课程探索 | 按校区、院系、BR/Distribution 类别、评分、工作量、难度和评论数量筛选 |
| 课程画像与比较 | 查看官方先修、共修、排除课程及其他要求，再比较模拟画像 |
| 偏好推荐 | 根据高评分、低负担、项目实践等偏好调整排序，展示实际偏好分与推荐理由 |
| 相似课程 | 对课程名称、院系、标签、关键词建立 TF-IDF 向量，使用余弦相似度检索 |
| 数据质量 | 查看字段、日期、范围、主键、关联关系等检查的通过/失败及记录数量 |
| 结果导出 | 下载课程画像、推荐结果和质量报告的 CSV 文件 |

## 三个校区的分类与课程要求

| 校区与范围 | 官方体系 | 本项目处理 |
| --- | --- | --- |
| St. George · Faculty of Arts & Science | 五类 Breadth Requirement（BR1–BR5） | 保存官方编号与类别名称 |
| UTM · Mississauga | Distribution Requirement：Humanities、Social Science、Science | 保存该课程官方分布类别，可能不止一类 |
| UTSC · Scarborough | UTSC 自身的五类 Breadth Requirement | 保存原有类别名称，不转换成 St. George 的 BR 编号 |

课程可有多个分类或未列出分类；不根据院系猜测。先修条件中的 **AND/OR、最低分、学分门槛、许可与限制**均按目录文字保留。“官方未列出先修字段”不等于已确认可以注册。跨校区的要求认定、实际开课和注册资格仍应查看官方目录、ACORN/Timetable 与院系规定。

数据来源、三校区分类和更新方法详见 [来源与范围](docs/data_sources.md)。课程快照见 [data/reference/uoft_courses.json](data/reference/uoft_courses.json)。

## 更新官方课程快照

日常运行无需联网，直接使用随版本保存的官方课程快照。需要核对最新目录时运行：

```bash
python scripts/update_catalog.py
python run_pipeline.py
```

更新器从三个官方 Academic Calendar 获取课程信息，校验后替换快照；获取失败时保留原快照。仅更新静态课程元数据，不抓取群聊或真实评价。

## v2 的改进

- **更可靠的数据处理：** 保留异常值供检查识别，避免把缺失字段转换为有效文本或把异常评分静默裁剪成合规数值。检查失败时阻止新的数仓发布，并保留诊断报告。
- **更稳健的推荐：** 用评论数量对课程均分进行平滑，排除已知无评论的课程；以确定性排序和与实际加减分对应的解释呈现推荐。
- **更有区分度的课程标签：** 根据评论提及比例与短语匹配打标签，处理简单否定，减少评论总量和宽泛词匹配的干扰。
- **更完整的交互：** 中文优先界面、筛选、课程对比、CSV 导出、缺失数据与空结果提示。
- **更易维护与复现：** 回归测试、Streamlit AppTest、GitHub Actions、独立开发依赖和指标文档。

## 数据流与仓库结构

```text
官方课程快照 + 模拟评价 / 现有原始 CSV
            │
         pandas ETL
            │
      数据质量检查与门禁 ──失败──> 保存报告并终止
            │通过
       NLP 关键词与标签
            │
       DuckDB 本地数仓
   ODS → DWD → DWS → ADS
            │
   偏好推荐 / 相似课程检索
            │
     Streamlit + Plotly
```

| 层 | 作用 | 示例 |
| --- | --- | --- |
| ODS | 保留源数据形态，便于追溯 | `ods_reviews_raw` |
| DWD | 标准化明细与课程、教师、学期维度 | `dwd_reviews_clean` |
| DWS | SQL 汇总课程、教师、院系指标 | `dws_course_summary` |
| ADS | 课程画像、默认推荐排序、质量报告 | `ads_course_profile` |

仓库使用本地 DuckDB 文件。指标公式在 Python 与独立 SQL 示例中保持一致；推荐阶段合并课程标签，再根据当次勾选偏好计算 `preference_score`。详见 [指标定义](docs/metrics_definition.md)、[数仓设计](docs/warehouse_design.md) 和 [数据字典](docs/data_dictionary.md)。

## 推荐逻辑

1. 计算课程均分、难度、工作量、实用性与评论数。
2. 使用全局评论均分与 10 条先验评论平滑课程评分，减少极少量评价带来的波动。
3. 计算 1–5 范围内的课程画像分，再组合为默认 `recommend_score`。
4. 根据显式偏好加减分，得到最终排序用的 `preference_score`。该分数可能超过 5。
5. 返回与评分规则一致的理由；相似课程检索单独使用 TF-IDF 与余弦相似度。

没有用户行为训练、协同过滤或大语言模型调用；评论支持权重反映样本数量，**不表示预测准确率**。推荐方法及权重均可在 [src/recommender.py](src/recommender.py) 中审阅。

## 使用已有 CSV

将符合 [数据字典](docs/data_dictionary.md) 的五张源表放入 `data/raw/`：

```text
courses_raw.csv
instructors_raw.csv
semesters_raw.csv
course_offerings_raw.csv
reviews_raw.csv
```

```bash
python run_pipeline.py --skip-generate
```

该参数复用原始文件。默认 `python run_pipeline.py` 会载入官方课程快照，并重新生成模拟教师、开课和评价数据。质量失败会返回非零退出状态，详情保存在 `data/processed/data_quality_report.csv`；修正源数据后再运行。已有 DuckDB 文件不会因门禁失败被覆盖。导入数据时，课程画像和质量报告均来自本地文件，不会上传至外部服务。

## 开发与验证

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
python run_pipeline.py
```

测试覆盖数据清洗、完整性检查、异常阻断、评分平滑、标签/否定处理、排序解释、相似检索边界和看板交互。GitHub Actions 同时验证测试与完整数据流水线。

```text
data/reference/      版本化的官方课程元数据及来源清单
scripts/             官方目录更新入口
app/                 Streamlit 看板
src/                 ETL、质量检查、标签、画像、推荐
sql/                 分层表与分析查询示例
docs/                指标、字典、设计、项目介绍与版本记录
tests/               单元与应用回归测试
run_pipeline.py      一键构建入口
```

## English overview

**CourseInsight helps University of Toronto students compare courses using official catalogue requirements and explainable analytics.** It combines real course metadata from St. George, UTM and UTSC with synthetic feedback, using Python, pandas, DuckDB, scikit-learn, Streamlit and Plotly.

The public dataset contains 200 official course records (80 St. George, 60 UTM, 60 UTSC), alongside 60 fictional instructors, 800 simulated offerings and 12,000 synthetic reviews. As described by the maintainer, review themes are inspired by course-selection discussions in student-union, alumni and peer groups; the repository contains no original group messages or authentic student review records. The pipeline standardizes source data, validates integrity before publishing the warehouse, extracts TF-IDF keywords and proportion-based rule tags, and ranks courses using explicit preferences. Review-count smoothing limits the influence of sparse ratings. Similar courses are retrieved using TF-IDF cosine similarity.

The dashboard supports campus-aware breadth/distribution filtering, official prerequisite and related requirement lookup, course comparison, explanations, CSV exports and quality-report exploration. Campus classification systems remain separate. Evaluation samples and ranking scores use synthetic data and transparent heuristics; it does not claim measured improvements in student outcomes or recommendation accuracy.

## 后续方向

真实数据接入与隐私处理、基于真实反馈的离线评估、用户历史偏好、增量 ETL，以及数据量增长后引入调度与分布式计算。以上为后续方向，当前版本无需外部服务即可运行。
