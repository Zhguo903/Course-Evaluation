# 真实历史课程评价：来源、字段及使用范围

核验日期：**2026-10-13，America/Toronto**。本次已下载并验证三份公开 CSV，导入 **64,554 份历史调查报告的数值事实**。它们是学生公开整理的历史官方课程评价结果副本，**不是本项目直接从大学当前官方评价系统取得的数据，也未逐条与登录后的官方报告复核**。

当前版本保留数值、课程标识、时间、报告数量及可追溯来源；不生成评分，也不把工作量解释成课程难度。推荐筛选仍由当前官方课程目录和开课记录决定。

## 找到并实际下载的资源

2025-02-04，学生记者在 [本人发布的公开数据帖](https://www.reddit.com/r/UofT/comments/1ihe5tu/) 中分享了历史 Arts & Science 评价表，并邀请读者研究数据。评论者 `_O-o-f` 在同一帖中公开提供了补充数据的 [Google Drive 文件夹](https://drive.google.com/drive/folders/1Pg7qk7N2PvKaqMsGjw09El9jsWVmHPEB)。本次采用的是该文件夹中的三个校区原始报告 CSV，不是记者的 Google Sheet，也不把评论者的副本等同于记者自行验证的数据。

三份文件均通过公开下载链接返回 HTTP 200，无登录、无 UTORid、无私有群聊资料。字节级 SHA-256、原始列名、年份／学期分布和精确下载链接记载于 [评价清单](../data/reference/evaluation_manifest.json)。

| 公开源文件 | 实际报告行数 | 源文件内年份 | 对应当前目录的报告／课程数 |
| --- | ---: | --- | ---: |
| [artsci.csv](https://drive.google.com/file/d/1A2yh-XeIeUTrudYHfAHvclj39S_kdlzJ/view) | 40,727 | 2012–2024 | 33,006／3,414 |
| [mississaugua.csv](https://drive.google.com/file/d/1jnrCY8UjQpvqeswR3xXB-9tE4JIcwSp_/view) | 10,997 | 2013、2016–2024 | 9,851／1,592 |
| [scarborough.csv](https://drive.google.com/file/d/1pGV_LFagFQikou8n0xkumVQ_VyyRTIo7/view) | 12,830 | 2014–2024 | 11,235／1,485 |
| 合计 | **64,554** | 各校区覆盖不同 | **54,092／6,491** |

UTM 文件仅有一条 2013 年记录，不能据此声称完整覆盖 2013 年。Arts & Science 和 UTM 的 2024 年记录包含 Winter／Summer，UTSC 的 2024 年记录另含 Fall。年份跨度也不代表每门课、每学期都有评价。

另外 **10,462 条历史报告无法对应当前所选本科目录**，仍保留为 `match_status="unmatched"`、`course_code=""`，以原始 `source_course_code` 溯源；可能涉及已停开、改号、范围外课程或源字段错误。不会按课程标题或相近代码强行匹配，也不会跨校区匹配。

## 原始字段及题目映射

源 CSV 含课程代码、课程／教学班标签、年、学期、教师姓、邀请人数、调查回复数及各题平均值。**没有个人学生逐条回应，也没有学生自由文本评论字段。** 导入结果不保留教师姓或独立的课程标题字段；原始 `source_course_code` 若含源站错误混入的标题，按原样作为溯源字段保留。

对照 [大学官方评价题目表](https://teaching.utoronto.ca/course-evaluations/ce-items/)，三个指标映射如下。它们均为五级量表的历史均值，不是通用五星评分。

| 规范字段 | 含义 | Arts & Science 原列 | UTM 原列 | UTSC 原列 | 高分含义 |
| --- | --- | --- | --- | --- | --- |
| `overall_score` | 整体学习体验质量 | `INS6` | `Item 6` | `INS6` | 学习体验更好 |
| `workload_score` | 与其他课程相比的工作量 | `ARTSC2` | `Course Workload` | `UTSC2` | 工作量更重 |
| `recommendation_score` | 向其他学生推荐课程的意愿 | `ARTSC3` | `I would recommend this course` | `UTSC3` | 推荐意愿更强 |

三项均保留 **1–5** 原量表；空白值转为 `null`，不填零。现有数据缺少 207 个工作量值及 200 个推荐值；整体学习体验值在本次副本中均有数值。此处的 `overall_score` 评价学习体验，不能改名为“教授评分”；`workload_score` 不能改名为“难度”。[题目含义及量表来源](https://teaching.utoronto.ca/course-evaluations/ce-items/)。

回复数原列分别为 `Number Responses`、`Number of Survey Responses`、`Number of Responses`，统一保留为 `response_count`；`Number Invited` 保留为 `invited_count`。这些是报告级调查数量，文件没有提供每道题的独立回复数，因此不能假设所有回复者都回答了每道题。

## 可核验的数值样例

下表来自公开源文件第 2 行，仅展示数值事实与标识；可通过相应文件自行核对。

| 来源／原行号 | 原始课程代码 | 年／学期 | 学习体验 | 工作量 | 推荐 | 回复／邀请 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| artsci.csv／2 | AFR250Y1 | 2024 Winter | 4.9 | 3.2 | 4.8 | 18／37 |
| mississaugua.csv／2 | ENG356H5 | 2024 Summer | 4.4 | 3.4 | 4.8 | 5／14 |
| scarborough.csv／2 | THRC50H3 | 2024 Fall | 4.2 | 3.5 | 4.5 | 6／18 |

每条导入记录另含 `source_id`、`source_row_number`、源文件链接、获取时间及稳定 `evaluation_id`。标识根据源文件哈希与原始 CSV 行号生成；修订后的源文件可明确与此前版本区分。

## 已保留的异常及统计限制

原文件包含同一教学班的多个教师报告。移除教师姓名后，它们可能具有相同课程、学期、回复人数和均值；这些是源报告，不应擅自当作重复垃圾删除，也不应把回复数求和称为独立学生人数。`cohort_id` 依据源课程／教学班标签、校区、年份及学期生成，用于提示报告可能共享受访群体。

当前保留以下明确标记：7,294 条记录属于多报告 cohort；348 条无法可靠识别教学班；13 条没有邀请人数；1 条源报告的回复数大于邀请人数。源数字不被自动修正，`quality_flags` 记录异常。报告条数是报告条数，**不是学生人数、独立 respondent 总数或课程完整覆盖率**。

文件夹中的 `combined.csv`、`lecture_sections_combined.csv`、`dept_combined.csv` 未导入。实际查看发现合并文件的 `Response Ratio` 存在与列名直觉不符的倒数计算，部分汇总文件把不适用题目填成零。当前版本使用三个校区的原始报告数值，不复用这些预先汇总的结果。

## 许可和当前可访问范围

原记者邀请读者研究公开数据，但该邀请不能自动扩展为对评论者文件的完整再分发许可。**本次未找到这三份 CSV 的独立开放许可证**。项目保留数值事实和来源，不把原始 CSV 全文、教师名单或调查评论加入仓库；也不宣称大学已对该副本背书。若要直接再分发原始文件，应先核实发布者及原始来源的使用条件。

大学官方说明：部分学院的历史评价可通过 Quercus 查看，教师可选择不分享，少于五份回复的结果也不分享。这意味着公开副本可能缺少合法不公开的报告，不能把缺失评价理解成零分或差评。[官方学生访问说明](https://teaching.utoronto.ca/course-evaluations/for-students/)。

[UofT Index](https://uoftindex.com/) 提供方便的评价浏览入口，但其公开条款要求数据协作取得书面授权，禁止未经授权的自动抽取和复制数据库；其首页开放 API 仍列为规划中。因此目前适合作为外部查询链接，未作为本项目的批量数据源。[该站使用条款](https://uoftindex.com/terms)，[数据方法说明](https://uoftindex.com/methodology)。

## 重建和离线读取

现有应用直接读取已验证的本地数值快照，不会在启动时向第三方发起批量请求。手动保存上述三个公开 CSV 后，可离线重建：

```bash
python scripts/import_evaluations.py --source-dir /path/to/public-csvs
```

目录需包含 `artsci.csv`、`mississaugua.csv`、`scarborough.csv`；研究阶段文件名的 `evals_` 前缀也可识别。若明确需要重新下载公开副本：

```bash
python scripts/import_evaluations.py --fetch
```

`--fetch` 只读取上述公开链接，将原始文件暂存于临时目录；默认命令必须明确选择来源，不会静默联网。下载／解析／匹配／数值检查失败时保留现有快照。

应用使用 `load_evaluation_snapshot()` 读取 [历史数值记录](../data/reference/course_evaluations.json) 与 [评价清单](../data/reference/evaluation_manifest.json)。两个文件均不存在时返回“资料不可用”；只缺一个文件、SHA-256 不符、来源或数量校验失败时明确报错，不把损坏数据当作“没有评价”。
