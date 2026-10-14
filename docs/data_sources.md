# 数据来源、范围与解释

核验日期：2026-10-13，多伦多时间。项目以真实官方课程目录和课表帮助学生快速找课；学生会、校友及课友群的交流场景用于理解产品需求，当前数据未由群消息生成。

## 官方目录

| 校区及范围 | 课程数 | 来源 |
| --- | ---: | --- |
| St. George Faculty of Arts & Science 本科 | 5,368 | [官方课程搜索](https://artsci.calendar.utoronto.ca/search-courses) |
| UTM 本科 | 2,491 | [官方课程搜索](https://utm.calendar.utoronto.ca/course-search) |
| UTSC 本科 | 2,178 | [官方课程搜索](https://utsc.calendar.utoronto.ca/search-courses) |
| 合计 | 10,037 | 三个未筛选的完整目录 |

其他 St. George 专业学院及研究生目录不在范围内。目录所属校区不保证实际授课地点，例如异地项目包含 H0 / Y0 代码。

课程完整打印导出与各校区搜索分页进行核对：St. George 共 178 个完整页加末页 28 条；UTM 共 83 个完整页加末页 1 条；UTSC 共 72 个完整页加末页 18 条，每页 30 条。校验总数和首尾顺序，未按课程标题或固定学科抽样。

课程保存官方代码、名称、分类和条件类要求，`description` 留空，完整介绍通过 `source_url` 阅读。`requirement_notes` 从普通介绍中保留完整条件句及必要的短上下文；带 NOTE 标签的备注块和独立备注字段保持原文，不截断 AND / OR、成绩门槛或学期限定。每条附来源日期，文件附 SHA-256。要求字段空白表示官方未列出，不代表确定不存在条件。

## Department / 学科

通过官方 sitemap 收集学科章节，按章节中实际课程代码建立映射。`department` 保存第一个匹配到的官方学科或项目名称，`department_source_url` 指向该章节；多个匹配分组分别保存在 `subject_areas` JSON 数组中，不拼接到 `department`。该分组不一律等于行政管理部门，也不表示课程归属的唯一行政单位。

10,015 门课程映射到官方章节，`department_source=official_calendar_section`；剩余 22 门使用带 `(course subject)` 标识的课程前缀分组，`department_source=course_prefix`，其 `subject_areas` 为空数组、`department_source_url` 为空，没有推测院系。所有回退代码与章节来源列于目录 manifest。

## 分类体系

| 体系 | 分类 |
| --- | --- |
| St. George Arts & Science BR | 1 Creative and Cultural Representations；2 Thought, Belief and Behaviour；3 Society and its Institutions；4 Living Things and Their Environment；5 The Physical and Mathematical Universes |
| UTM Distribution | Science；Humanities；Social Science |
| UTSC Breadth | Arts, Literature and Language；History, Philosophy and Cultural Studies；Social and Behavioural Sciences；Natural Sciences；Quantitative Reasoning |

保留课程官方列出的多个类别；空白不会补造类别。官方原文分别保存在 `breadth_requirements` 与 `distribution_requirements`，`requirement_categories` 保存该体系的类别名称数组，`breadth_categories` 仅保存 St. George 的 BR 编号。页面分类选项带有校区前缀，防止跨体系混用。跨校区学分能否满足个人毕业要求，需要按所属学院规则核对。

## 修读要求、Level 与学分

保存先修、共修、排除课程、建议准备、注册限制和限制性备注。保持英文原始条件并规范空白，不将复杂的 AND / OR、成绩门槛或项目限制简化成自动资格判断。

St. George / UTM 的数字代码用于 Level，UTSC 的 A / B / C / D 对应 100 / 200 / 300 / 400。0xx 课程保留为 0，页面标为预科 / 其他。

标准 H / Y 代码分别对应 0.5 / 1.0 学分，`credit_basis=course_code_HY` 说明依据。非标准 COP / PDC / INT / CIP 及 0xx 课程不直接套用此规则，53 门保留未知，依据标为 `not_listed_nonstandard_course`；ISP010H5 官方明确无学分，记录为 0，依据标为 `explicit_calendar_description`。`credit_note` 解释特殊情况。

## 开课状态

[官方 Timetable Builder](https://ttb.utoronto.ca/) 是独立于目录的来源。当前覆盖 Fall 2026、Winter 2027 和 2026–2027 全年，包含 7,093 条课程学期开课记录；完整响应与官方分页统计一致。记录数不能等同于目录中开课课程数，且两个官方系统会存在代码覆盖差异。

- `offered`：覆盖学期有未取消的官方开课记录，包括已满或注册关闭的课程。
- `cancelled`：有记录，但课程或所有主要教学班已取消。
- `not_found`：在该校区、所选学期的完整已发布课表中未检索到。
- `unknown`：所选学期未发布、未覆盖或数据不完整。

全年课程计入秋季和冬季筛选。默认覆盖全部已发布学期；只要存在一条未取消记录，汇总状态为已发布开课。每个学期的独立状态保存在 `offering_status_by_session`。

页面不是实时余位查询，也不替代 ACORN 注册。详细接口与完整性机制见 [课表来源说明](timetable_sources.md)。

## 更新与可用数据集

日常运行只读取已核验快照。显式更新使用 `scripts/update_catalog.py` 和 `scripts/update_timetable.py`，再运行 `run_pipeline.py`；出错保留已核验版本。GitHub 发布页提供含来源链接的课程 CSV、DuckDB 和源代码。历史版本含模拟评价，v3 已移除相关数据与算法。

第三方数据库是否适合接入、更新频率和许可情况见 [数据源调研](data_source_research.md)。

## 新增学生评价与学习资料 · v3.2

课程目录与开课仍以官方来源为准。新增的 70,453 条历史调查报告来自公开社区整理的副本，未与 UTORid 后的原始报告逐条复核；54,196 条报告精确关联 6,505 门当前课程，16,257 条保留未匹配。保留原题维度、1–5 量表、年份、回复数和源异常，不预测当前难度或成绩，不计算跨来源综合分。[历史评价来源及字段](feedback_data_sources.md)。

另导入同一位 CS ’25 作者的 28 条公开个人推荐评价，用中文转述并链接原帖，原始个人推荐尺度为 1–10。作者身份及选课情况未独立核验，不能视为多位学生的共识。旧 MAT137、MAT235 代码没有强行对应到当前替代课。[个人评价原帖](https://www.reddit.com/r/UofT/comments/1kjq8ji/rating_and_reviewing_every_course_i_took_at_uoft/)。

752 条学习资源中，746 条对应 575 门当前课程，另有 6 条通用或未关联历史入口；共有 748 个唯一 URL，以大纲、讲义、课程网站为主，也包含明确核验的练习和旧试卷。所有资源带核验日期和访问条件；资料内容与试卷全文不存入仓库。详见 [学习资源说明](learning_resources.md)。
