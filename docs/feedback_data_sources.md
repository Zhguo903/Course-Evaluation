# 真实历史课程评价：来源、字段及使用范围

核验日期：**2026-10-14，America/Toronto**。本次已下载并验证四份公开 CSV，导入 **70,453 份历史调查报告的数值事实**。它们是学生公开整理的历史官方课程评价结果副本，**不是本项目直接从大学当前官方评价系统取得的数据，也未逐条与登录后的官方报告复核**。

当前版本保留数值、课程标识、时间、报告数量及可追溯来源；不生成评分，也不把工作量解释成课程难度。推荐筛选仍由当前官方课程目录和开课记录决定。

## 找到并实际下载的资源

2025-02-04，学生记者在 [本人发布的公开数据帖](https://www.reddit.com/r/UofT/comments/1ihe5tu/) 中分享了历史 Arts & Science 评价表，并邀请读者研究数据。评论者 `_O-o-f` 在同一帖中公开提供了补充数据的 [Google Drive 文件夹](https://drive.google.com/drive/folders/1Pg7qk7N2PvKaqMsGjw09El9jsWVmHPEB)。本次采用的是该文件夹中的三个校区原始报告 CSV，以及第四份 Engineering（APSC）原始报告 CSV；不是记者的 Google Sheet，也不把评论者的副本等同于记者自行验证的数据。

四份文件均通过公开下载链接返回 HTTP 200，无登录、无 UTORid、无私有群聊资料。字节级 SHA-256、原始列名、年份／学期分布和精确下载链接记载于 [评价清单](../data/reference/evaluation_manifest.json)。

| 公开源文件 | 实际报告行数 | 源文件内年份 | 对应当前目录的报告／课程数 |
| --- | ---: | --- | ---: |
| [artsci.csv](https://drive.google.com/file/d/1A2yh-XeIeUTrudYHfAHvclj39S_kdlzJ/view) | 40,727 | 2012–2024 | 33,006／3,414 |
| [mississaugua.csv](https://drive.google.com/file/d/1jnrCY8UjQpvqeswR3xXB-9tE4JIcwSp_/view) | 10,997 | 2013、2016–2024 | 9,851／1,592 |
| [scarborough.csv](https://drive.google.com/file/d/1pGV_LFagFQikou8n0xkumVQ_VyyRTIo7/view) | 12,830 | 2014–2024 | 11,235／1,485 |
| [fas.csv（APSC / Engineering）](https://drive.google.com/file/d/1wMut9mPuEKMDdS_PXhVvN-94061w2sTe/view) | 5,899 | 2013–2024 | 104／14 |
| 合计 | **70,453** | 各来源覆盖不同 | **54,196／6,505** |

UTM 文件仅有一条 2013 年记录，不能据此声称完整覆盖 2013 年。Arts & Science 和 UTM 的 2024 年记录包含 Winter／Summer，UTSC 的 2024 年记录另含 Fall。年份跨度也不代表每门课、每学期都有评价。

Engineering 文件虽名为 `fas.csv`，实际 `Division` 原列为 `APSC`。其 104 条报告精准对应当前目录中的 14 门 MAT／MSE 课程，补充了此前没有历史评价的 14 门课；另外 5,795 条 Engineering 报告仍属未匹配，不能当作新增目录覆盖。源清单明确标注 `origin_faculty="APSC / Engineering"`，不把它们误称为 Arts & Science 调查。

另外 **16,257 条历史报告无法对应当前所选本科目录**，仍保留为 `match_status="unmatched"`、`course_code=""`，以原始 `source_course_code` 溯源；可能涉及已停开、改号、范围外课程或源字段错误。不会按课程标题或相近代码强行匹配，也不会跨校区匹配。

## 原始字段及题目映射

源 CSV 含课程代码、课程／教学班标签、年、学期、教师姓、邀请人数、调查回复数及各题平均值。**没有个人学生逐条回应，也没有学生自由文本评论字段。** 导入结果不保留教师姓或独立的课程标题字段；原始 `source_course_code` 若含源站错误混入的标题，按原样作为溯源字段保留。

对照 [大学官方评价题目表](https://teaching.utoronto.ca/course-evaluations/ce-items/)，三个指标映射如下。它们均为五级量表的历史均值，不是通用五星评分。

| 规范字段 | 含义 | Arts & Science 原列 | UTM 原列 | UTSC 原列 | 高分含义 |
| --- | --- | --- | --- | --- | --- |
| `overall_score` | 整体学习体验质量 | `INS6` | `Item 6` | `INS6` | 学习体验更好 |
| `workload_score` | 与其他课程相比的工作量 | `ARTSC2` | `Course Workload` | `UTSC2` | 工作量更重 |
| `recommendation_score` | 向其他学生推荐课程的意愿 | `ARTSC3` | `I would recommend this course` | `UTSC3` | 推荐意愿更强 |

Engineering 的整体学习体验仍为 `INS6`，工作量对应官方第三道学院题 `APSC003`。该文件没有对应的课程推荐题，5,899 条 `recommendation_score` 全部保留 `null`，不会拿其他题目代替。[Engineering 题目及量表来源](https://teaching.utoronto.ca/course-evaluations/ce-items/)。

三项均保留 **1–5** 原量表；空白值转为 `null`，不填零。现有数据缺少 207 个工作量值及 6,099 个推荐值（其中 5,899 个因 Engineering 源没有此题）；整体学习体验值在本次副本中均有数值。此处的 `overall_score` 评价学习体验，不能改名为“教授评分”；`workload_score` 不能改名为“难度”。[题目含义及量表来源](https://teaching.utoronto.ca/course-evaluations/ce-items/)。

回复数原列分别为 `Number Responses`、`Number of Survey Responses`、`Number of Responses`，统一保留为 `response_count`；`Number Invited` 保留为 `invited_count`。这些是报告级调查数量，文件没有提供每道题的独立回复数，因此不能假设所有回复者都回答了每道题。

## 可核验的数值样例

下表来自公开源文件第 2 行，仅展示数值事实与标识；可通过相应文件自行核对。

| 来源／原行号 | 原始课程代码 | 年／学期 | 学习体验 | 工作量 | 推荐 | 回复／邀请 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| artsci.csv／2 | AFR250Y1 | 2024 Winter | 4.9 | 3.2 | 4.8 | 18／37 |
| mississaugua.csv／2 | ENG356H5 | 2024 Summer | 4.4 | 3.4 | 4.8 | 5／14 |
| scarborough.csv／2 | THRC50H3 | 2024 Fall | 4.2 | 3.5 | 4.5 | 6／18 |
| fas.csv／2 | APS106H1（未匹配） | 2024 Summer | 4.2 | 3.3 | 未列出 | 21／59 |

每条导入记录另含 `source_id`、`source_row_number`、源文件链接、获取时间及稳定 `evaluation_id`。标识根据源文件哈希与原始 CSV 行号生成；修订后的源文件可明确与此前版本区分。

## 已保留的异常及统计限制

原文件包含同一教学班的多个教师报告。移除教师姓名后，它们可能具有相同课程、学期、回复人数和均值；这些是源报告，不应擅自当作重复垃圾删除，也不应把回复数求和称为独立学生人数。`cohort_id` 依据源课程／教学班标签、校区、年份及学期生成，用于提示报告可能共享受访群体。

当前保留以下明确标记：8,409 条记录属于多报告 cohort；384 条无法可靠识别教学班；13 条没有邀请人数；1 条源报告的回复数大于邀请人数。源数字不被自动修正，`quality_flags` 记录异常。报告条数是报告条数，**不是学生人数、独立 respondent 总数或课程完整覆盖率**。

文件夹中的 `combined.csv`、`lecture_sections_combined.csv`、`dept_combined.csv` 未导入。实际查看发现合并文件的 `Response Ratio` 存在与列名直觉不符的倒数计算，部分汇总文件把不适用题目填成零。当前版本使用四个源文件的原始报告数值，不复用这些预先汇总的结果。

## 许可和当前可访问范围

原记者邀请读者研究公开数据，但该邀请不能自动扩展为对评论者文件的完整再分发许可。**本次未找到这四份 CSV 的独立开放许可证**。项目保留数值事实和来源，不把原始 CSV 全文、教师名单或调查评论加入仓库；也不宣称大学已对该副本背书。若要直接再分发原始文件，应先核实发布者及原始来源的使用条件。

大学官方说明：部分学院的历史评价可通过 Quercus 查看，教师可选择不分享，少于五份回复的结果也不分享。这意味着公开副本可能缺少合法不公开的报告，不能把缺失评价理解成零分或差评。[官方学生访问说明](https://teaching.utoronto.ca/course-evaluations/for-students/)。

[UofT Index](https://uoftindex.com/) 提供方便的评价浏览入口，但其公开条款要求数据协作取得书面授权，禁止未经授权的自动抽取和复制数据库；其首页开放 API 仍列为规划中。因此目前适合作为外部查询链接，未作为本项目的批量数据源。[该站使用条款](https://uoftindex.com/terms)，[数据方法说明](https://uoftindex.com/methodology)。

## 重建和离线读取

现有应用直接读取已验证的本地数值快照，不会在启动时向第三方发起批量请求。手动保存上述四个公开 CSV 后，可离线重建：

```bash
python scripts/import_evaluations.py --source-dir /path/to/public-csvs
```

目录需包含 `artsci.csv`、`mississaugua.csv`、`scarborough.csv`、`fas.csv`；研究阶段文件名的 `evals_` 前缀也可识别。若明确需要重新下载公开副本：

```bash
python scripts/import_evaluations.py --fetch
```

`--fetch` 只读取上述公开链接，将原始文件暂存于临时目录；默认命令必须明确选择来源，不会静默联网。下载／解析／匹配／数值检查失败时保留现有快照。

应用使用 `load_evaluation_snapshot()` 读取 [历史数值记录](../data/reference/course_evaluations.json) 与 [评价清单](../data/reference/evaluation_manifest.json)。两个文件均不存在时返回“资料不可用”；只缺一个文件、SHA-256 不符、来源或数量校验失败时明确报错，不把损坏数据当作“没有评价”。

## 2026-10-14 的扩展核查结果

本次新增的是 Engineering 源的 **14 门当前课程／104 份匹配报告**，不是新年份的数据。所选三个校区本科目录仍维持原有范围；其余 Engineering 记录保留为未匹配历史事实。

另实际下载了记者原始公开 [XLSX 文件](https://docs.google.com/spreadsheets/d/1WeC4kw6ymgpR4ErYrKBp2Sixw4d8vcKg/edit?gid=1212526924)，文件标题为 *Course Evaluation Data - Maeve Ellis and Mekhi Quarshie / The Varsity.xlsx*。其 All Years 工作表中，`Division=ARTSC` 且课程非空的报告有 40,723 条，年份仍为 2012–2024，覆盖当前目录的 3,414 门课程全部已被现有 Arts & Science CSV 覆盖，故不重复导入。该计数是实际符合上述条件的记录，不把空白尾行、排名页或示例页当作评价。

重新核对公开 Drive 文件夹仍为七份 CSV：四份原始报告文件已使用，另三份是前述派生汇总。本次未在这些已核验公开资源中发现 2025–2026 年的新原始报告。

[ASSU 官方 Anti-Calendar 页面](https://assu.ca/wp/anti-calendar/) 提供学生会历史评价的说明及档案入口；页面明确表示常规最后一版为 2011–2012。其历史题目包含七级量表及百分比分布，与当前 1–5 指标含义不同，不能直接转换或混合。此次档案页／PDF 的实时抓取未成功，因此仅列为后续历史资料线索，不声称已导入或完整核验其数值。

其他核查包括官方评价入口、公开学生评课网站与 GitHub 数据线索。目前未发现能够在现有来源之外、经过核验并直接扩大当前课程覆盖的更新开放评价库；有些网站只是空白展示模板，有些要求登录或授权。接下来更适合增加能核对课程代码、年份和来源的公开旧教案、习题及考试资料链接，而不是用重复报告或推测分数填补评价空白。
