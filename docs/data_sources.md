# 数据来源、三校区范围与使用口径

## 项目目标与社区参考

CourseInsight 面向多伦多大学学生，旨在把分散的选课经验与官方课程信息整理成可比较的课程画像，减少查阅课程分类、先修条件和学习负担信息时的重复工作。

根据维护者提供的背景说明，模拟评价的内容设计参考了学生会、校友及课友群中常见的选课交流主题：工作量、考试难度、教学方式、项目实践与课程实用性。**仓库没有导入原始群聊记录，也不把生成样本标注为真实学生评价或群聊摘录。** 当前代码按课程特征和这些主题生成可复现的演示记录，不执行群消息采集、账号登录或群聊文本提取。

| 数据 | 来源与用途 |
| --- | --- |
| 课程代码、名称、学分、校区 | 官方 Academic Calendar 的公开课程信息 |
| 广度/分布类别、先修及相关要求 | 官方课程详情，保留原文条件与来源 |
| 评分、难度、工作量、实用性与评论 | 参考维护者描述的社区交流主题生成的模拟样本 |
| 教师、学期、开课、容量与人数 | 为数据工程演示生成的虚构记录，不是官方开课与授课安排 |
| 画像与推荐分 | 基于模拟评价的公开启发式计算，不是推荐准确率或真实 GPA 预测 |

## 覆盖范围

默认快照包含 **200 门选取课程：St. George 80、UTM 60、UTSC 60**，覆盖统计、计算机、经济、数学、生物、心理、英语和历史等方向。它是用于展示三校区选课信息整合的样本，不是全校全部课程、当前学期开课清单或专业毕业要求全集。

来源：

- [St. George · Faculty of Arts & Science Academic Calendar](https://artsci.calendar.utoronto.ca/)
- [University of Toronto Mississauga Academic Calendar](https://utm.calendar.utoronto.ca/)
- [University of Toronto Scarborough Academic Calendar](https://utsc.calendar.utoronto.ca/)

每门课保存完整代码、官方课程链接和 `source_retrieved_at`，便于核对。源页面可能在之后发生更新，应以届时适用的官方目录为准。

## 三个分类体系

### St. George · Faculty of Arts & Science

保留五类 Breadth Requirement：

1. Creative and Cultural Representations
2. Thought, Belief and Behaviour
3. Society and its Institutions
4. Living Things and Their Environment
5. The Physical and Mathematical Universes

编号只用于 St. George 文理学院的类别，不覆盖所有 St. George 学院。详见 [官方学位要求](https://artsci.calendar.utoronto.ca/hbahbsc-requirements)。

### UTM · Mississauga

使用 Distribution Requirement：Humanities、Social Science、Science。课程可被目录列为多个类别，保存全部官方类别，不强制推断为单一分类。详见 [UTM 官方说明](https://www.utm.utoronto.ca/registrar/enrolment/choosing/distribution)。

### UTSC · Scarborough

保留 UTSC 自身的 Breadth Requirement 名称：Arts, Literature and Language；History, Philosophy and Cultural Studies；Social and Behavioural Sciences；Natural Sciences；Quantitative Reasoning。课程可列出多个类别。详见 [UTSC 官方术语说明](https://utsc.calendar.utoronto.ca/glossary) 和 [广度要求说明](https://www.utsc.utoronto.ca/aacc/breadth-requirements)。

三个校区的类别不直接转换。跨校区学分如何满足本人的学位要求需要对应校区认定；本项目不自动判定跨校区等效性。

## 先修及注册相关要求

保存官方字段 `prerequisite`、`corequisite`、`exclusion`、`recommended_preparation`、`enrolment_requirements` 和 `requirement_notes`。括号、AND/OR 关系、最低成绩、已修学分、项目资格与教师/院系许可要求按原文保留。

`prerequisite_status=not_listed` 表示来源页面没有列出该字段，**不能据此断言无先修要求或保证可以注册**。表内的排除课程也不表示可以替代先修条件。最终以官方课程页、ACORN、Timetable 与院系规定核对。

## 更新与追溯

- `data/reference/uoft_courses.json`：随版本保存的课程元数据快照。
- `data/reference/catalog_manifest.json`：来源、覆盖范围与更新时间等记录。
- `python scripts/update_catalog.py`：从官方目录重新获取并校验快照；失败时保留旧快照。
- `python run_pipeline.py`：从本地快照生成原始课程表和模拟评价，再执行 ETL、质量门禁、数仓发布。

日常运行无需网络，不把私有群聊或学生数据发送给外部服务。使用自行提供的源 CSV 时，用 `--skip-generate` 保留输入。历史 v2.0.0 的随机课程名和随机校区元数据已由本版本的官方课程快照替代，模拟评价随真实课程集合重新生成。
