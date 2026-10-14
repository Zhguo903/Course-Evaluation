# 学习资源与维护

截至 2026-10-14，索引共有 **752 条资源，748 个唯一 URL**：746 条精确关联当前官方目录的 **575 门课程**，另 6 条通用或未关联历史入口。它是持续扩充的精选索引，尚未覆盖全部课程；一门课可有多期资料，一个文件也可由官方明确关联多门课。[各校区课程覆盖统计](data_coverage.md)。

| 类型 | 条目数 |
| --- | ---: |
| 教学大纲 | 672 |
| 讲义 | 18 |
| 课程资料页 | 16 |
| 课程网站 | 17 |
| 学生指南 | 10 |
| 练习／例题入口 | 4 |
| 模拟试卷 | 3 |
| 历年试卷 | 8 |
| 通用试卷入口／学习支持 | 4 |

多数新增资料是公开大纲。明确作为练习或试卷分类的 15 条链接涉及 8 门课程；其余课程网站内也可能有习题，但没有逐项核验的内容不会冒充单独试题记录。

页面可按资料类型与标题筛选，每课最多展示 20 条，并始终提供本课完整资料 CSV；优先展示练习、模拟与旧卷，同类型按资料年份排列。顺序不代表质量评分。

## 本次实际核验的来源

- [Rotman 历年大纲](https://rotmancommerce.utoronto.ca/current-students/choosing-your-courses/course-outlines-archive/)及[经济系课程档案](https://www.economics.utoronto.ca/index.php/index/undergraduate/previousyears)：每课选少量最近学期与代表教学班。[商科、经济及物理批次](resource_expansion_business_physics.md)。
- [CS 大纲索引](https://web.cs.toronto.edu/undergraduate/courses/outlines)、数学／统计教师公开课程页：大纲、练习、模拟题与材料入口。[St. George 批次](resource_expansion_sg.md)。
- [UTSC Biology](https://www.utsc.utoronto.ca/biosci/course-syllabi)、[Chemistry](https://www.utsc.utoronto.ca/physsci/chemistry-course-syllabi)、[Psychology 档案](https://www.utsc.utoronto.ca/psych/syllabus-archive)及环境、食品、物理等官方列表：每门课选择最新可公开读取的一份大纲。[UTM／UTSC 批次](resource_expansion_utm_utsc.md)。
- UTM [Alvaro Nosedal 教学页](https://mcs.utm.utoronto.ca/~nosedal/teaching.html)、[Pierre Desrochers 课程页](https://geog.utm.utoronto.ca/desrochers/)与 [CSSC 学生指南](https://cssc.utm.utoronto.ca/resources/)。学生指南属于具名观点与建议，不作为全体学生评价。
- [PHY354](https://www.physics.utoronto.ca/~poppitz/poppitz/PHY354.html)与[PHY450](https://www.physics.utoronto.ca/~poppitz/poppitz/PHY450.html)教师发布的旧试卷；准确年份未列出时保持未知。

数据库保存标题、完整代码、校区、类型、学期、发布者、访问条件、核验日期、权利说明和原始链接。资料内容在原站阅读；项目不镜像教材、题目、解答或试卷全文。公开访问不自动等于开放许可。CS 大纲索引要求仅供参考、不分发或再利用大纲信息，本项目仅保存课程、期次与原站链接。

旧材料的成绩分配、教学计划和先修要求不能作为当前政策。经济系秋冬档案的整体标题虽为 Winter，具体资料已按 F/S/Y 分为实际秋、冬或全年；夏季 F/S 保留为夏季分段。旧 MAT137Y1 与 MAT235Y1 不自动改配到类似代码或其他校区。图书馆试卷内容仍可能需 UTORid，入口会明确标注，不登录抓取。

## 扩展与更新

批次脚本必须显式运行才会联网。沿官方实际索引提取链接，核对完整课程代码、校区、期次与来源；PDF 检查 HTTP/MIME 和文件签名，无法读取、空 HTML、错误代码或不明校区的目标排除并保留审计。SG 补充脚本还需可选的 `pypdf` 包，以核对 PDF 自身课程标识；它不是页面运行依赖。

```bash
python scripts/discover_business_physics_resources.py
# SG 复核额外需要：pip install pypdf
python scripts/discover_sg_resources.py
python scripts/discover_sg_resources.py --append-extra
python scripts/discover_sg_resources.py --audit-existing
python scripts/discover_utm_utsc_resources.py
python scripts/merge_resources.py \
  --input data/reference/resources_business_physics_expansion.json \
  --input data/reference/resources_sg_expansion.json \
  --input data/reference/resources_utm_utsc_expansion.json
python scripts/verify_support.py
python run_pipeline.py
```

合并先核验已发布支持快照哈希，不能顺便重新认证无关学生评价或来源变动；再按校区、完整代码及无 fragment 的 URL 去重并验证，记录批次哈希、唯一课程／URL 数及分类统计。验证失败或通常写入异常时保留已发布文件。多个文件逐个替换，有并发读取或进程崩溃时严格 loader 会拒绝不一致版本，不静默接受。

有意修改个人评价或来源登记后，先核对来源，再独立使用 `python scripts/verify_support.py --refresh-manifest` 更新支持哈希。刷新 hash 本身不代替来源核验。正常应用启动和离线 pipeline 不自动抓取网站。
