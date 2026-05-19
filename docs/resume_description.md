# Resume Description

## 中文版本

项目名称：校园课程评价数据仓库与智能选课推荐系统 CourseInsight

项目描述：
基于 Python、pandas、DuckDB 和 Streamlit 从零搭建校园课程评价数据仓库与推荐系统，模拟生成 200 门课程、60 位教师、800 个开课记录和 12,000 条课程评论数据；完成 raw 到 processed 的 ETL 清洗流程，设计 ODS-DWD-DWS-ADS 分层数仓模型，并通过 SQL 构建课程、教师、院系等主题汇总指标。结合 TF-IDF、规则情感分析和标签体系生成课程画像，实现基于用户偏好的课程推荐和相似课程检索，并开发 Streamlit 可视化看板展示核心指标、课程画像、推荐结果和数据质量报告。

可用于简历要点：
- 设计并实现 ODS-DWD-DWS-ADS 本地数据仓库，沉淀课程评价、教师、院系等多粒度指标。
- 使用 pandas 完成数据清洗、字段标准化、评分范围校验、重复数据处理和文本规范化。
- 使用 DuckDB 编写 SQL 指标计算逻辑，构建课程画像、推荐分和数据质量 ADS 表。
- 基于 TF-IDF 和规则标签体系实现课程关键词提取、课程标签生成和相似课程推荐。
- 使用 Streamlit + Plotly 搭建数据产品原型，展示课程指标、推荐结果和数据质量监控。

## English Version

Project: CourseInsight: Campus Course Review Data Warehouse & Recommendation System

Description:
Built an end-to-end analytics engineering project using Python, pandas, DuckDB, scikit-learn, and Streamlit. Generated synthetic campus course review data including 200 courses, 60 instructors, 800 offerings, and 12,000 reviews. Implemented ETL pipelines, designed an ODS-DWD-DWS-ADS warehouse architecture, and created SQL-based course, instructor, and department summary metrics. Developed TF-IDF keyword extraction, rule-based sentiment labels, course tags, preference-based recommendations, and similar-course retrieval. Delivered an interactive Streamlit dashboard for course profiles, recommendations, metrics exploration, and data quality monitoring.

Resume bullets:
- Designed a layered ODS-DWD-DWS-ADS data warehouse in DuckDB for synthetic campus review analytics.
- Built pandas ETL pipelines for schema normalization, score validation, deduplication, and text cleaning.
- Developed SQL metrics and ADS course profile scores for rating, workload, usefulness, GPA friendliness, and recommendation ranking.
- Implemented TF-IDF keyword extraction, rule-based NLP tags, and cosine-similarity course recommendations.
- Created a Streamlit and Plotly dashboard to operationalize analytics outputs and data quality checks.
