# 学习资源与维护

当前整理 21 条资源：15 条关联当前官方目录中的 11 门课程，另 6 条为校区通用入口或历史资料，覆盖三个校区。来源核验日期为 2026-10-13。这是精选链接目录，尚未覆盖全部课程；同一课程可以关联不同资料，同一份讲义也可能服务多门课。

数据库保存标题、完整课程代码、校区、资源类型、学期、发布者、访问要求、核验日期、权利说明及原始链接，不复制教材、文章、作业答案或考试全文。用户应在原站阅读，并以当期课程公告为准。资料缺失不表示该课没有学习资源。

## 主要来源

- [CSC110／CSC111 官方讲义](https://www.teach.cs.toronto.edu/~csc110y/fall/notes/)
- [CSC148 官方讲义](https://www.teach.cs.toronto.edu/~csc148h/notes/)
- [UTM CSC108 历史课程站](https://mcs.utm.utoronto.ca/~108s21/)
- [UTM CSSC 学生指南示例](https://cssc.utm.utoronto.ca/resources/csc108/)
- [MAT223 开放教材](https://siefkenj.github.io/IBLLinearAlgebra/)
- [UTSC 课程入口](https://cms-pcrs.utsc.utoronto.ca/)
- [UTSC 辅导学习小组](https://www.utsc.utoronto.ca/ctl/facilitated-study-groups-program)
- [图书馆历年考试入口说明](https://guides.library.utoronto.ca/tspace/aboutpastexams)

CSSC 的 CSC108、CSC148、MAT102 三篇指南是具名学生观点与学习建议，不是官方注册规则，也不是代表全体学生的数值评价。MAT223 教材明确采用 CC BY-SA 4.0；本项目仍只保存链接。其他资料未确认开放许可时，不因公开可读而默认允许复制。

历史 syllabus 的成绩分配、前置课和教学安排不代表当期政策。旧 MAT137Y1 不在当前目录，其资料作为历史入口保留，课程代码字段为空，不自动映射到 MAT137H5 或替代课程。图书馆考试实际内容需要有效 UTORid，使用范围受原站限制；项目只存入口，不登录抓取或再分发试卷。辅导小组也须核对当期安排，不向所有课程批量关联。

## 扩展与更新

从官方教师课程站、CSSC 的课程页及公开源码、图书馆资源说明逐步扩展。维护者先打开原始来源，核对完整代码与校区、标题、学期、访问要求和权利范围；失效链接应删除或标明，不凭搜索摘要认定可用。没有当前代码对应关系的旧资料保持未关联。

人工核验后编辑 `data/reference/course_resources.json`，再显式更新校验清单并重建数据库：

```bash
python scripts/verify_support.py --refresh-manifest
python run_pipeline.py
```

刷新 hash 只是确认文件版本，不代替来源核验。保留核验日期与限制说明，检查通过后再发布；应用启动仅读取快照，不自动抓取网站或绕过登录。
