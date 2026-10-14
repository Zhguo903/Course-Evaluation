# 项目介绍与简历表述

## 中文项目介绍

**CourseInsight｜多伦多大学课程探索与可解释选课推荐系统**

面向多伦多大学学生构建课程信息整合与推荐原型，结合 St. George、UTM 和 UTSC 的官方课程目录，以及参考学生会、校友及课友群常见选课反馈生成的模拟评价，帮助学生更高效地比较感兴趣的课程。整理 200 门真实课程的校区、广度/分布类别、先修及相关注册要求，保留官方来源并区分三校区的分类体系。基于 Python、pandas、DuckDB 与 Streamlit 完成数据清洗、质量校验、分层数仓、课程画像与偏好排序，提供课程筛选、比较、相似检索和结果导出。

## 个人网站精简版

为多伦多大学学生整合三校区官方课程信息与社区交流主题下的模拟选课反馈。支持按校区和 BR/Distribution 分类探索课程、查阅先修条件，并结合学习负担和内容偏好进行比较与推荐。

## 简历要点

- 整合 St. George、UTM 和 UTSC 的 200 门官方课程记录，保存广度/分布类别、先修/共修/排除要求及可追溯来源。
- 设计 ODS–DWD–DWS–ADS 本地数仓，保留复杂课程要求原文，避免跨校区分类误映射。
- 使用 TF-IDF、比例标签与评分平滑，为 12,000 条模拟评价构建课程画像和可解释偏好排序。
- 开发支持校区、类别筛选、课程比较及 CSV 导出的 Streamlit 看板，并以质量门禁和自动化测试验证数据流程。

## English description

**CourseInsight | University of Toronto Course Explorer & Explainable Recommendations**

Built a course-information and recommendation prototype for University of Toronto students. Integrated official course metadata from St. George, UTM and UTSC, including campus-specific breadth/distribution categories, prerequisites, corequisites, exclusions and other enrolment requirements. Used synthetic feedback inspired by student-union, alumni and peer-group discussion themes, as described by the maintainer, to demonstrate course profiles and preference-based rankings. Implemented ETL, validation, a layered DuckDB warehouse and a Streamlit dashboard for course filtering, comparison, similarity search and CSV exports.

- Integrated 200 official course records with source links and retrieval dates while keeping campus classification systems separate.
- Preserved complete prerequisite and enrolment condition wording through the analytics warehouse.
- Developed explainable rankings from 12,000 synthetic reviews using TF-IDF features, rule tags and rating smoothing.
- Delivered campus-aware exploration and comparison with automated integrity and application checks.

## 表述依据

课程元数据来自官方目录，200 门为选取样本。社区信息参考背景由维护者说明；仓库不含原始群聊消息或真实学生评价。教师、开课与评价记录为模拟数据，GPA 友好度与职业相关性为启发式指标；没有真实选课效率或推荐准确率提升的实测数据。
