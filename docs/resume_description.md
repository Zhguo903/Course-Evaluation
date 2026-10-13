# 项目介绍与简历表述

## 中文项目介绍

**CourseInsight｜课程评价分析与可解释选课推荐系统**

基于 Python、pandas、DuckDB 与 Streamlit 构建本地课程评价数据产品原型。使用覆盖 200 门课程、60 位教师、800 条开课记录及 12,000 条评论的模拟数据，完成数据清洗、质量校验、ODS–DWD–DWS–ADS 分层建模和 SQL 指标分析。结合 TF-IDF 关键词提取、规则标签、评论数量平滑与用户偏好加权，实现课程画像、可解释推荐及相似课程检索，并通过交互式看板支持课程筛选、对比和结果导出。

## 个人网站精简版

将课程评分与文字评论整理为可比较的课程画像，通过学习负担、课程难度和内容偏好辅助选课。项目串联数据清洗、DuckDB 分层数仓、文本分析与交互式看板，完整展示从模拟原始数据到可解释推荐的数据产品流程。

## 简历要点

- 设计 ODS–DWD–DWS–ADS 本地数仓，使用 pandas 标准化明细数据，使用 DuckDB SQL 汇总课程、教师与院系指标。
- 构建覆盖字段、日期、评分范围及表间关联的数据质量检查，保存异常报告并在检查失败时阻止数仓发布。
- 结合 TF-IDF、评论提及比例标签与评分平滑，实现基于显式偏好的推荐、排序解释和相似课程检索。
- 开发 Streamlit + Plotly 看板，提供多条件筛选、课程比较和 CSV 导出，并通过回归测试与 GitHub Actions 验证核心流程。

## English description

**CourseInsight | Course Review Analytics & Explainable Recommendations**

Built a local analytics engineering prototype with Python, pandas, DuckDB and Streamlit. Used synthetic data covering 200 courses, 60 instructors, 800 offerings and 12,000 reviews to implement ETL, integrity checks, layered ODS–DWD–DWS–ADS modeling and SQL analytics. Combined TF-IDF keywords, proportion-based rule tags, review-count rating smoothing and explicit preference scoring to deliver course profiles, explainable rankings and similar-course retrieval. Developed an interactive dashboard for filtering, comparison, exports and data-quality inspection.

- Designed a layered DuckDB warehouse and reusable course, instructor and department metrics.
- Implemented data-quality checks and a publication gate that preserves failure diagnostics.
- Developed preference-based ranking, score-aligned explanations and TF-IDF similarity retrieval.
- Delivered a Streamlit dashboard with regression tests and GitHub Actions verification.

## 表述依据

数据规模为默认模拟生成规模；GPA 友好度与职业相关性是启发式指标。当前版本没有真实用户运营数据或推荐效果评估结果，因此不使用准确率提升、真实成绩改善等未经验证的表述。
