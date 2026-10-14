# 商科、经济与物理公开资料扩展 · 2026-10-14

本批次保留 **302 条公开 PDF 链接，精确关联 166 门当前 St. George 目录课程**。每条保存完整课程代码、原始索引、学期、访问条件、核验日期及限制；仓库不镜像文件内容。

| 来源 | 资料条数 | 内容 |
| --- | ---: | --- |
| [Rotman Commerce 官方历年大纲](https://rotmancommerce.utoronto.ca/current-students/choosing-your-courses/course-outlines-archive/) | 154 | 历史 course outlines，每门课最多选两个学期，每个学期保留一个教学班代表 |
| [经济系官方课程档案](https://www.economics.utoronto.ca/index.php/index/undergraduate/previousyears) | 140 | 从实际 2023–2025 夏季／冬季索引提取大纲，每课最多两个最新学期；秋冬档案按课程末尾 F/S/Y 分开标注，夏季 F/S 保留为夏季分段 |
| [PHY354 教师课程站](https://www.physics.utoronto.ca/~poppitz/poppitz/PHY354.html)、[PHY450 教师课程站](https://www.physics.utoronto.ca/~poppitz/poppitz/PHY450.html) | 8 | 教师公开发布的过去期中与期末试卷 |

所有 302 个目标实际返回 HTTP 200/206，读取前 1,024 字节确认 `%PDF-` 文件标记，同时记录 Content-Type 与最终 URL。只临时检查文件前缀，不保存、摘录或分发试卷和大纲全文。索引可以随网站更新变化，核验日期不等于未来持续可访问。

经济系必须使用从官网首页导航实际取得的 `/index.php/index/` 路径；搜索引擎中也出现 `/index.php/indec/` 路径，该路径的下载目标会返回 HTTP 200 空 HTML，不能当成可读 PDF。正式批次已沿真实官网导航重新取源并核验全部目标。

物理旧试卷的准确年份未在索引列出，保留 “Historical exam (year not specified)”。PHY354 索引中的部分文件名仍有旧编号 351；它们由当前索引明确作为 PHY354 历史参考列出，限制字段说明这一点，不能认定为某学期现行考试。历史教学安排与成绩分配也不能作为当前政策。

重现本批次：

```bash
python scripts/discover_business_physics_resources.py
```

命令显式联网，仅沿发布者实际索引提取链接，并与当前完整课程代码精确匹配。核验记录见 [批次清单](../data/reference/resources_business_physics_expansion.manifest.json)，资料元数据见 [链接批次](../data/reference/resources_business_physics_expansion.json)。脚本不在应用启动时运行。
