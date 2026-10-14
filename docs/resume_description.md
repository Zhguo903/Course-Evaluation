# 项目介绍与简历表述

## 中文项目介绍

CourseInsight 是面向多伦多大学学生的课程查找工具。项目围绕学生会、校友及课友群中常见的选课需求，整合 St. George Arts & Science、UTM 和 UTSC 的完整官方本科目录与已发布课表，让学生通过校区、课程级别、学科和 BR / Distribution 快速筛选课程，比较修读要求并核对是否开课。

当前版本整理 10,037 门官方课程及 7,093 条真实开课记录，保留来源链接与核验时间，区分三校区分类体系及未知状态。使用 Python、pandas、DuckDB 和 Streamlit 完成来源采集、完整性核验、原子数据发布、条件匹配与交互页面。数据核验于 2026-10-13，不含模拟评价。

## 个人网站精简版

为多伦多大学学生整合三校区 10,037 门官方本科课程与真实课表。支持按校区、Level、Department 和 BR / Distribution 快速找课，查看先修要求、开课状态并对比导出。

## 简历要点

- 整合三校区完整官方本科目录与课表，构建包含 10,037 门课程和 7,093 条开课记录的可追溯数据集。
- 通过目录分页核对、课表总数交叉校验、SHA-256 与覆盖范围检查，阻止不完整数据覆盖已核验版本。
- 使用 DuckDB 与 Streamlit 实现多条件筛选、学期状态、匹配理由、课程对比和 CSV 导出，并通过自动化测试验证关键交互。

## English description

Built CourseInsight, a course finder for University of Toronto students, using complete official undergraduate catalogues for St. George Arts & Science, UTM and UTSC. Integrated 10,037 catalogue courses and 7,093 timetable records with source links and retrieval dates. Implemented campus, level, academic-subject and breadth/distribution filters, transparent matching reasons, offering status, course comparison and CSV export with Python, pandas, DuckDB and Streamlit.

Validated catalogue completeness against official pagination and timetable counts against the official pageable API. Used snapshot hashes, explicit unknown states and atomic database publication to preserve verified data when refreshes fail.

## 表述边界

“全部课程”限于三个已列明的本科目录；数据规模是快照统计，不是推荐准确率或选课效率提升的实测结果。项目需求参考社区交流场景，当前课程事实来自官方来源，不声称群消息或生成评价为真实学生反馈。没有真实成绩、难度或工作量数据时不作相关预测。
