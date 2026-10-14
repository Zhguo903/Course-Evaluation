# 多伦多大学找课数据源调研

核验日期：**2026-10-13，America/Toronto**。本文区分“目录中存在的课程”“某学期已发布的开课记录”和“学生评价”。三类信息的来源、更新频率和可用范围不同。

## 当前采用的方案

本项目以**三校区官方本科 Calendar 建立课程目录，以官方 Timetable Builder 标注已发布学期的开课情况**。默认展示全部目录课程，学生再按校区、课程级别、学术领域／department、BR 或 Distribution 筛选；开课状态作为独立条件。推荐理由来自所选条件和官方要求，不生成评分、难度或工作量数据。

本次目录快照共 **10,037 门课程**：St. George Arts & Science 5,368 门、UTM 2,491 门、UTSC 2,178 门。这里的“全量”指三个所选本科 Calendar 的未筛选课程目录，不包含 U of T 的所有研究生课程或 St. George 的其他专业学院。快照数量、来源和分页核验记录见项目的 [目录清单](../data/reference/catalog_manifest.json)。

开课快照另含 **7,093 条记录，涉及 6,093 个不同的校区／课程组合**。同一门课程在不同学期出现会产生多条开课记录，不能把 7,093 当作不同课程数量。完整性记录见 [开课清单](../data/reference/timetable_manifest.json)。

## 可以用的数据源

| 来源 | 可提供的信息 | 项目用途与判断 |
| --- | --- | --- |
| [St. George Faculty of Arts & Science Calendar](https://artsci.calendar.utoronto.ca/search-courses) | 课程编号、名称、学术领域、BR、先修／共修／排除课程等 | 当前课程目录主源；覆盖所选 Arts & Science 本科范围 |
| [UTM Calendar](https://utm.calendar.utoronto.ca/course-search) | 课程编号、名称、Program Area／Department、Distribution、选课要求等 | 当前 UTM 本科目录主源；保留 UTM 的 Distribution 体系 |
| [UTSC Calendar](https://utsc.calendar.utoronto.ca/search-courses) | 课程编号、名称、学术领域、Breadth、选课要求等 | 当前 UTSC 本科目录主源；保留 UTSC 的 Breadth 体系 |
| [官方 Timetable Builder](https://ttb.utoronto.ca/) | 已发布学期、开课记录、教学班、取消标记等 | 当前开课状态主源，与 Calendar 分开采集 |
| [Courseography](https://github.com/Courseography/courseography) | 先修关系可视化、课表工具、Calendar／Timetable 解析实现 | 活跃的参考项目；不是本项目事实数据的替代来源 |
| [Cobalt datasets](https://github.com/cobalt-uoft/datasets) | 历史课程等 JSON 数据集 | 仓库已于 2020-05-16 归档，只适合历史结构参考 |
| [Nikel datasets](https://github.com/nikel-api/nikel-datasets) | 历史课程等结构化数据 | 最近 push 为 2022-03-11 UTC；不作为 2026 年主源 |
| [官方 Course Evaluations](https://teaching.utoronto.ca/course-evaluations/for-students/) | 部分学院向学生提供的历史评价结果 | 需通过 Quercus／UTORid 等官方入口访问，不能当成完整公开评价数据库 |

Calendar 的 BR／Distribution 名称以所属校区为准，三个校区的分类不能直接视为同一个毕业要求体系。跨校区课程是否能满足本人项目的学位要求，仍需按本人的学院及项目规定核对。

## 官方开课 API：可验证，但不是稳定性承诺

本次从 [Timetable Builder 官方客户端](https://ttb.utoronto.ca/) 观察并实际验证了 `https://api.easi.utoronto.ca/ttb` 的请求形式。发现的是官方网站正在使用的公开访问接口，**未发现可据此保证长期兼容的公开 SDK 或版本化开发者契约**；因此本项目保留离线快照和明确刷新流程。

| 已验证接口 | 作用 |
| --- | --- |
| [`GET /reference-data`](https://api.easi.utoronto.ca/ttb/reference-data) | 获取官方当前发布的学期、校区和 division 标识 |
| `POST /getCourses` | 按 division 和学期获取未筛选的全部开课记录 |
| `POST /getPageableCourses` | 获取分页结果及官方总数，用于交叉核验下载完整性 |
| `GET /findById?id=…` | 查看单条开课源记录；项目中的每条记录保留对应链接 |

三校区对应的官方 division 分别为 `ARTSC`、`ERIN`、`SCAR`。本次源站发布 Fall 2026（`20269`）、Winter 2027（`20271`）及全年 Fall–Winter 2026–2027（`20269-20271`），这些值来自官方返回结果，不由当前日期推测。各校区下载数为 3,772、1,692、1,629；合并查询和九个校区／学期组合的数量均已与官方分页接口的总数核对。具体请求、校验和刷新方法见 [开课来源说明](timetable_sources.md)。

应用中的“已开课”表示存在未取消的已发布记录；满员或关闭选课仍属于已开课。取消、完整检索后未找到、数据未知分别保留独立状态。全年课会计入其所跨越的两个学期。缺失文件、损坏快照或未发布学期不能被解释成“未开课”。快照不是实时余位信息，也不自动证明学生符合选课资格。

## 现成开源项目应怎样使用

**Courseography 适合参考课程关系和交互设计。** 核验时仓库仍有近期活动，GitHub 元数据显示最近 push 为 2026-10-13；代码许可证为 **GPL-3.0**。其 README 提供 Calendar／Timetable 解析及数据库构建步骤，可以研究实现方式；代码许可也不能自动代表校方源数据的许可。本项目当前使用自行采集的官方事实字段。[项目说明与许可证](https://github.com/Courseography/courseography)，[GitHub 仓库元数据](https://api.github.com/repos/Courseography/courseography)。

**Cobalt 适合历史数据与字段设计参考。** 维护者已声明项目不再维护，datasets 仓库标为归档；旧 README 中“自动更新”的介绍不能证明它在 2026 年仍持续更新。[维护者仓库说明](https://github.com/cobalt-uoft/datasets)。

**Nikel 的 datasets 仓库仍可访问，但新鲜度不足。** 核验时它未归档，GitHub `pushed_at` 为 `2022-03-11T01:30:20Z`。这里是 UTC 时间，不应把仓库其他元数据变化当作课程数据刷新证明；当前目录、先修要求和开课情况应回到官方来源核对。[Nikel datasets](https://github.com/nikel-api/nikel-datasets)，[GitHub 仓库元数据](https://api.github.com/repos/nikel-api/nikel-datasets)。

## v3.1 已新增的评价与学习资料

本次进一步研究找到可直接下载的公开三校区历史问卷副本：64,554 条报告，54,092 条精确对应当前目录的 6,491 门课程。它们来自公开社区整理，不等于当前官方开放 API，也未与登录后的校方报告逐条复核。另有 28 条来自同一作者的公开个人评价和 21 条学习资源链接。原始维度、年份、访问条件与限制分别登记，缺失保持未知，不计算跨来源综合分。详见 [完整来源与导入说明](feedback_data_sources.md)。

## 学生评价、群聊和准确性边界

官方说明指出，学生通过 Quercus 查看部分学院的既往评价；并非所有学院都分享数据，教师可选择不分享，少于五份回应的结果也不分享。因此本次没有发现可以据此宣称“三校区完整公开学生评价库”的官方数据源，项目不加入推测的评分、难度或工作量；现已导入的历史数值来源及范围见上节。[官方学生评价访问说明](https://teaching.utoronto.ca/course-evaluations/for-students/)。

学生会、校友群和课友群可以帮助理解学生的找课需求。当前版本的课程事实字段来自官方来源，**群聊主题及旧版生成评价不作为当前真实课程数据或推荐排序的证据**。若后续获得可使用的真实评价材料，应另外记录评价来源、采集时间、适用学期及可验证范围。

目录保留课程编号、名称、分类、要求等事实元数据及原始 `source_url`，`description` 字段当前留空；完整课程介绍通过官方链接阅读，不宣称本项目保存了所有课程的介绍全文。先修要求保留条件文本，官方未列出的字段显示为“未列出”，不自动改写成“无要求”。

当前仍有两类明确标注的数据缺口：**22 门课程的学术领域使用课程代码前缀作为备用标签**，界面明确说明它是 subject prefix；**53 门课程的学分无法从已验证字段中明确确定**，保留未知值。以上数量可在项目目录及清单中核对。

## 后续维护

课程目录与开课快照分别刷新，记录来源、时间和完整性证明。新学期优先重新核验官方已发布学期；课程要求变更以对应 Calendar 为准。学生看到的推荐应清楚展示匹配条件、要求原文、开课状态和官方链接，使其能够快速缩小范围并复核，而不是依赖无法追溯的分数。
