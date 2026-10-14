# UTM 与 UTSC 公开课程资料扩充记录

本批次只保存公开原站的链接与核验元数据，不保存或转发 PDF 正文、教材、答案及受限试卷。课程完整代码与校区均逐条匹配当前官方课程目录；不把旧代码、课程前缀或其他校区自动当作同一门课。每门 UTSC 课程只取官方索引中学期最新且可访问的一份大纲；同一文件被官方明确列给多门课时保留各课程关联，并分别报告链接数与课程数。

主要来源为 [UTSC Biology 大纲索引](https://www.utsc.utoronto.ca/biosci/course-syllabi)、[Chemistry](https://www.utsc.utoronto.ca/physsci/chemistry-course-syllabi)、[Environmental Science](https://www.utsc.utoronto.ca/physsci/environmental-science-course-syllabi)、[Food & Environmental Studies](https://www.utsc.utoronto.ca/physsci/food-environmental-studies-course-syllabi)、[Physics & Astrophysics](https://www.utsc.utoronto.ca/physsci/physics-astrophysics-course-syllabi)、[Psychology/Neuroscience 公开档案](https://hive.utsc.utoronto.ca/public/psych/syllabi/)；后者的官方关联入口为 [Psychology syllabus archive](https://www.utsc.utoronto.ca/psych/syllabus-archive)。UTM 来源为 [Alvaro Nosedal 教学索引](https://mcs.utm.utoronto.ca/~nosedal/teaching.html)、[Pierre Desrochers 官方 Geography 课程页](https://geog.utm.utoronto.ca/desrochers/)与 [CSSC 学生资源](https://cssc.utm.utoronto.ca/resources/)。CSSC 页面属于学生观点，不代表全体学生或官方注册要求。

年份来自官方列表的学期标题；Psychology 文件名含明确学期编码时优先文件名，避免索引误放造成误标。关联核验依据可见课程标签、明确文件名与当前目录。PDF 仅发起最多读取 512 字节的公开 GET，记录 HTTP/MIME 并验证 `%PDF-` 签名；不读取全文。HTTP 404、登录页面、无 PDF 签名及不匹配的旧学分后缀均不收录。旧材料只能参考，不能证明当期授课、考核、先修或教材要求；未知学期保持空值，不能补成当前学年。公开访问不等于开放授权。

可手动运行 `python scripts/discover_utm_utsc_resources.py --verified-at YYYY-MM-DD` 重查；最多三请求并发、全局限速，缓存位于临时目录。正常应用启动与离线 pipeline 不执行网络抓取。合并前还需审阅失败列表、确认当前课程代码、去重现有资源，并使用主项目的支持资料核验流程更新完整性摘要。

UTM Psychology 当前公开页面仅指向统一 Timetable，未发现可核验的课程级公开 archive；UTM Economics 的 syllabus supplement 为部门通用规则，未重复附到每一门课以扩大数量。未猜测受限 CIS 或 Quercus 文件地址。

## 核验统计与来源审计

下列数字是本次新增文件的实际条目数、课程数及 URL 数；`sources` 保留每个具体列表的候选数，`failures` 保留未收录原因。所有成功 PDF 的 HTTP、MIME 与签名检查记录仅缓存在临时目录，不镜像 PDF 文件。

```json
{
  "verified_at": "2026-10-14",
  "dataset_sha256": "12529a1603d75e5241d4eeef6cefc5f843e5b34fdc93d5dcb9fb88fb6a082b55",
  "records": 348,
  "unique_course_campus_pairs": 334,
  "unique_urls": 345,
  "by_campus": {
    "Mississauga": 33,
    "Scarborough": 315
  },
  "courses_by_campus": {
    "Mississauga": 19,
    "Scarborough": 315
  },
  "by_type": {
    "student_guide": 7,
    "course_site": 13,
    "lecture_notes": 12,
    "course_materials": 1,
    "syllabus": 315
  },
  "by_course_prefix": {
    "AST": 6,
    "BIO": 80,
    "CHM": 32,
    "CSC": 6,
    "EES": 50,
    "EST": 13,
    "FST": 10,
    "GGR": 11,
    "NRO": 12,
    "PHY": 23,
    "PSC": 3,
    "PSY": 86,
    "STA": 16
  },
  "source_index_count": 77,
  "raw_pdf_links_in_indexes": 3867,
  "current_syllabus_candidates": 3456,
  "pdf_urls_checked": 441,
  "pdf_check_success": 320,
  "pdf_check_failure": 121,
  "successful_pdf_http_mime": {
    "206 application/pdf": 320
  },
  "unavailable_syllabus_courses": [
    "BIOB20H3",
    "BIOC29H3",
    "BIOC70H3",
    "BIOD06H3",
    "BIOD07H3",
    "BIOD15H3",
    "BIOD24H3",
    "BIOD32H3"
  ],
  "skipped": {
    "not_current_or_ambiguous_course": 326,
    "historical_credit_suffix_mismatch": 2
  },
  "sources": {
    "https://www.utsc.utoronto.ca/biosci/course-syllabi": {
      "pdf_links": 865,
      "current_course_candidates": 828
    },
    "https://www.utsc.utoronto.ca/physsci/chemistry-course-syllabi": {
      "pdf_links": 482,
      "current_course_candidates": 466
    },
    "https://www.utsc.utoronto.ca/physsci/environmental-science-course-syllabi": {
      "pdf_links": 493,
      "current_course_candidates": 476
    },
    "https://www.utsc.utoronto.ca/physsci/food-environmental-studies-course-syllabi": {
      "pdf_links": 56,
      "current_course_candidates": 56
    },
    "https://www.utsc.utoronto.ca/physsci/physics-astrophysics-course-syllabi": {
      "pdf_links": 289,
      "current_course_candidates": 279
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20269/": {
      "pdf_links": 50,
      "current_course_candidates": 50
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20265/": {
      "pdf_links": 27,
      "current_course_candidates": 26
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20261/": {
      "pdf_links": 52,
      "current_course_candidates": 50
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20259/": {
      "pdf_links": 47,
      "current_course_candidates": 45
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20255/": {
      "pdf_links": 28,
      "current_course_candidates": 25
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20251/": {
      "pdf_links": 44,
      "current_course_candidates": 43
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20249/": {
      "pdf_links": 45,
      "current_course_candidates": 42
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20245/": {
      "pdf_links": 26,
      "current_course_candidates": 24
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20241/": {
      "pdf_links": 47,
      "current_course_candidates": 45
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20239/": {
      "pdf_links": 46,
      "current_course_candidates": 43
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20235/": {
      "pdf_links": 28,
      "current_course_candidates": 26
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20231/": {
      "pdf_links": 49,
      "current_course_candidates": 47
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20229/": {
      "pdf_links": 48,
      "current_course_candidates": 44
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20225/": {
      "pdf_links": 26,
      "current_course_candidates": 24
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20221/": {
      "pdf_links": 44,
      "current_course_candidates": 42
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20219/": {
      "pdf_links": 45,
      "current_course_candidates": 42
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20215/": {
      "pdf_links": 26,
      "current_course_candidates": 24
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20211/": {
      "pdf_links": 51,
      "current_course_candidates": 45
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20209/": {
      "pdf_links": 45,
      "current_course_candidates": 41
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20205/": {
      "pdf_links": 29,
      "current_course_candidates": 26
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20201/": {
      "pdf_links": 43,
      "current_course_candidates": 40
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20199/": {
      "pdf_links": 46,
      "current_course_candidates": 42
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20195/": {
      "pdf_links": 31,
      "current_course_candidates": 25
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20191/": {
      "pdf_links": 47,
      "current_course_candidates": 36
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20189/": {
      "pdf_links": 51,
      "current_course_candidates": 41
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20185/": {
      "pdf_links": 31,
      "current_course_candidates": 25
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20181/": {
      "pdf_links": 47,
      "current_course_candidates": 35
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20179/": {
      "pdf_links": 41,
      "current_course_candidates": 31
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20175/": {
      "pdf_links": 29,
      "current_course_candidates": 21
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20171/": {
      "pdf_links": 46,
      "current_course_candidates": 33
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20169/": {
      "pdf_links": 38,
      "current_course_candidates": 28
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20165/": {
      "pdf_links": 24,
      "current_course_candidates": 17
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20161/": {
      "pdf_links": 39,
      "current_course_candidates": 25
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20159/": {
      "pdf_links": 36,
      "current_course_candidates": 27
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20155/": {
      "pdf_links": 22,
      "current_course_candidates": 15
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20151/": {
      "pdf_links": 35,
      "current_course_candidates": 22
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20149/": {
      "pdf_links": 32,
      "current_course_candidates": 21
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20145/": {
      "pdf_links": 19,
      "current_course_candidates": 13
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20141/": {
      "pdf_links": 33,
      "current_course_candidates": 19
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20139/": {
      "pdf_links": 20,
      "current_course_candidates": 14
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20135/": {
      "pdf_links": 21,
      "current_course_candidates": 15
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20131/": {
      "pdf_links": 33,
      "current_course_candidates": 21
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20109/": {
      "pdf_links": 33,
      "current_course_candidates": 21
    },
    "https://hive.utsc.utoronto.ca/public/psych/syllabi/20105/": {
      "pdf_links": 14,
      "current_course_candidates": 10
    },
    "https://mcs.utm.utoronto.ca/~nosedal/256.html": {
      "pdf_links": 4,
      "current_course_candidates": 1
    },
    "https://mcs.utm.utoronto.ca/~nosedal/258.html": {
      "pdf_links": 18,
      "current_course_candidates": 1
    },
    "https://mcs.utm.utoronto.ca/~nosedal/260.html": {
      "pdf_links": 5,
      "current_course_candidates": 1
    },
    "https://mcs.utm.utoronto.ca/~nosedal/302.html": {
      "pdf_links": 3,
      "current_course_candidates": 1
    },
    "https://mcs.utm.utoronto.ca/~nosedal/313.html": {
      "pdf_links": 8,
      "current_course_candidates": 1
    },
    "https://mcs.utm.utoronto.ca/~nosedal/437.html": {
      "pdf_links": 15,
      "current_course_candidates": 1
    },
    "https://mcs.utm.utoronto.ca/~nosedal/457.html": {
      "pdf_links": 15,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/csc108": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/csc148": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/csc207": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/csc209": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/csc236": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/csc258": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/csc263": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/csc358": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/sta256": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://cssc.utm.utoronto.ca/resources/mat102": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-209-economic-geography-course/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-209-economic-geography-lectures-part-1/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-365-trade-and-globalization-course/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-365-trade-and-globalization-lectures-1-6/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-329-environment-and-the-roots-of-globalization-course/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-329-environment-and-the-roots-of-globalization-lectures/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-333-energy-and-society/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-333-energy-and-society-lectures-part-1/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-387-food-and-globalization-course/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-387-food-and-globalization-lectures-1-to-8/": {
      "html_verified": true,
      "current_course_candidates": 1
    },
    "https://geog.utm.utoronto.ca/desrochers/ggr-489-special-topics-in-human-geography-cities-industry-and-the-environment/": {
      "html_verified": true,
      "current_course_candidates": 1
    }
  },
  "failures": [
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOA01%20Syllabus_Summer%202025.pdf?csf=1&web=1&e=JIXlRp",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOA11%202025S%20SYLLABUS.pdf?csf=1&web=1&e=4mADpK",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOA11H3%20-%202024F%20SYLLABUS.pdf?csf=1&web=1&e=hcsmPp",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOA01%20F2024%20Syllabus%20(4).pdf?csf=1&web=1&e=z4vydj",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BioA11%20biology%20of%20humans%20(4).pdf?csf=1&web=1&e=05y1H8",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOA01%20Syllabus_Y2024.pdf?csf=1&web=1&e=klnxBx",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOA01%20Syllabus_F2023.pdf?csf=1&web=1&e=8MUKXq",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOB20%20SYLLABUS%20F2024.pdf?csf=1&web=1&e=jbRQIe",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOB33H3Y-2025_Summer_Syllabus.pdf?csf=1&web=1&e=mrtb9V",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOB34%20-%20Course%20Syllabus%20-%20Summer%202025.pdf?csf=1&web=1&e=5lzXgp",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOB20%20(Fall%202023).pdf?csf=1&web=1&e=Ab9b8I",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOB34%20Fall%202024%20Syllabus%20(1).pdf?csf=1&web=1&e=BAX2ix",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOB33H3Y%20Syllabus%202024%20Summer.pdf?csf=1&web=1&e=Zm2Dch",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOB34%20-%20Course%20Syllabus%20-%20Summer%202024.docx.pdf?csf=1&web=1&e=EzHLpU",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOB38%20Course%20Syllabus%20Winter%202025.pdf?csf=1&web=1&e=mJOrJa",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOB33H3F%20Syllabus%202023%20Fall%20(2).pdf?csf=1&web=1&e=4u7cxl",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOB34%20Fall%202023%20Syllabus%20-%202023_11_07.pdf?csf=1&web=1&e=lcOwWR",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOB38%20Course%20Syllabus%202024W.pdf?csf=1&web=1&e=UfrlIp",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOB50H3F-2024_Fall_Syllabus.pdf?csf=1&web=1&e=ViLAeD",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOB52%20Syllabus_Y2025.pdf?csf=1&web=1&e=bikRKF",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOB52%20Syllabus%20F2024.pdf?csf=1&web=1&e=yBdq3y",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOB50_Syllabus_Summer2024.pdf?csf=1&web=1&e=Jp6rhu",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOB52%202024S.pdf?csf=1&web=1&e=ONELuf",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOB50H3F-2023_Fall_Syllabus-20230904.pdf?csf=1&web=1&e=JrEheb",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOB52%20Syllabus%20%2723.pdf?csf=1&web=1&e=C6sqFG",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC12H3F-2024F%20Syllabus.pdf?csf=1&web=1&e=mR9OXF",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOC15H3%20Syllabus%202025.pdf?csf=1&web=1&e=bwTzpc",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOC12summercourse%20outline2024.pdf?csf=1&web=1&e=FAeeHt",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC12H3F-2023_Fall_Syllabus-September%202.pdf?csf=1&web=1&e=aLl3YO",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC15H3F-F2024%20Syllabus.pdf?csf=1&web=1&e=BKvaJX",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOC15%20Course%20Syllabus%20-%20Summer%202024.pdf?csf=1&web=1&e=mHuZbr",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC19H3F-2024F%20Syllabus.pdf?csf=1&web=1&e=3jcgQ5",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC15H3F-2023_Fall_Syllabus-20230918.pdf?csf=1&web=1&e=SzAY21",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOC20%20Course%20Syllabus%20-%20Summer%202025.pdf?csf=1&web=1&e=oCyntq",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC19%20Animal%20Developmental%20Biology%20Course%20Syllabus%20Fall%202023_09052023%20KGan.pdf?csf=1&web=1&e=B20Jxz",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC20%20Course%20Syllabus%20-%20Fall%202024%20(1).pdf?csf=1&web=1&e=H0OSGp",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC21%20-%20Course%20Syllabus%20-%20Winter%202025.docx.pdf?csf=1&web=1&e=ABAG8k",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC20%20Course%20Syllabus%20-%20Fall%202023%20(2).pdf?csf=1&web=1&e=tg0cf5",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC21%20-%20Course%20Syllabus%20-%20Winter%202024.docx.pdf?csf=1&web=1&e=VFUBZ5",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOC23%20Course%20Syllabus%20-%20Summer%202025.pdf?csf=1&web=1&e=94XotS",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC29_Introductory_Mycology_Syllabus_2023.pdf?csf=1&web=1&e=7mptOg",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC23%20Syllabus%20winter2025.pdf?csf=1&web=1&e=aGERKU",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC31H3S-2025_Winter_Syllabus-Jan2025.pdf?csf=1&web=1&e=chcLbi",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC32%20-%20Course%20Syllabus%20-%20Fall%202024.docx%20(2).pdf?csf=1&web=1&e=2jdBxD",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOC23%20Course%20Syllabus%20-%20Summer%202024.pdf?csf=1&web=1&e=BxepHx",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC31H3S-2024_Winter_Syllabus-20240105.pdf?csf=1&web=1&e=dMFdUs",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC32%20-%20Course%20Syllabus%20-%20Fall%202023.docx.pdf?csf=1&web=1&e=si3jK9",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC23%20Syllabus%20winter2024.pdf?csf=1&web=1&e=avYaG5",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC34H3S-2025_Winter_Syllabus-20250105.pdf?csf=1&web=1&e=kLpbyj",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC35_F2024%20syllabus.pdf?csf=1&web=1&e=lXTuTv",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC34%20syllabus%202024W.pdf?csf=1&web=1&e=h7qN5l",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC37%20Course%20Syllabus%202024F.pdf?csf=1&web=1&e=7EtP8O",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC35_syllabus-5.pdf?csf=1&web=1&e=4eBpTj",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC37%20Course%20Syllabus%202023.pdf?csf=1&web=1&e=sG6oRE",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC40H3S-2025_Winter_Syllabus.pdf?csf=1&web=1&e=9RrI00",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC39%20Syllabus%20-%20Winter%202025.pdf?csf=1&web=1&e=Vj8kNn",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC40H3S-2024_Winter_Syllabus.pdf?csf=1&web=1&e=Pyedv6",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC39%20Syllabus%20-%20Winter%202024.pdf?csf=1&web=1&e=f7mGYc",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOC51%202025%20Syllabus.pdf?csf=1&web=1&e=6HakeM",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC50H3F-2024_Fall_Syllabus.pdf?csf=1&web=1&e=W538Tg",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC54%202025%20Course%20syllabus.pdf?csf=1&web=1&e=0OSHMM",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC58H3%20syllabus%20Fall%202024.pdf?csf=1&web=1&e=KrHWpD",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC52%20Course%20Syllabus%202024F.pdf?csf=1&web=1&e=zsW6Wl",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC54%202024%20Course%20syllabus.pdf?csf=1&web=1&e=pXgk10",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC58H3%20syllabus%20Fall%202023.pdf?csf=1&web=1&e=TanRns",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC52%20Course%20Syllabus%202023.pdf?csf=1&web=1&e=v8uXIw",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC59H3F-2024_Fall_Syllabus.pdf?csf=1&web=1&e=tCUOlS",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC60%20syllabus%202025.pdf?csf=1&web=1&e=hYhplb",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC61H3%20Syllabus%20Fall%202024.pdf?csf=1&web=1&e=XAelpY",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC60%20Syllabus%202024%20Winter%20-%20UPDATED.pdf?csf=1&web=1&e=wmrDIC",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC61%20SYLLABUS%202024W.pdf?csf=1&web=1&e=iXMjbu",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC62H3%20syllabus%20Winter%202025.pdf?csf=1&web=1&e=Jqf6eO",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC63H3%20Syllabus%20Fall%202024.pdf?csf=1&web=1&e=uFBgJt",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC63H3%20Syllabus%20Fall%202023.pdf?csf=1&web=1&e=RFenKX",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOC70-Winter2024-Syllabus-Andrade-Jan5.pdf?csf=1&web=1&e=keKoQU",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOC90_syllabusWinter2025.pdf?csf=1&web=1&e=pPMEJh",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOD07H3%202024W%20SYLLABUS.pdf?csf=1&web=1&e=1WwpYL",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOC90%20syllabus%20Fall%202024.pdf?csf=1&web=1&e=pyd1hh",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOC90%20syllabus%20Fall%202023.pdf?csf=1&web=1&e=CGPatX",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD06%20Course%20Syllabus%202024F.pdf?csf=1&web=1&e=BHz52B",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOD06%202024W%20SYLLABUS.pdf?csf=1&web=1&e=EafP1Z",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOD12HF_course_syllabus_2025_Winter.pdf?csf=1&web=1&e=Ex0dPf",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOD15H3S-2025_Winter_Syllabus-20241210.pdf?csf=1&web=1&e=AAX8gU",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOD13%20syllabus_2023.pdf?csf=1&web=1&e=IJ33nZ",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOD12HF_course_syllabus_2024_Winter.pdf?csf=1&web=1&e=as32wm",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD17%20Course%20Syllabus%20-%20Fall%202024.pdf?csf=1&web=1&e=972Otu",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOD19H3S-2025_Winter_Syllabus-20250107_final.pdf?csf=1&web=1&e=hYYVSc",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOD17%20Course%20Syllabus%20-%20Fall%202023.pdf?csf=1&web=1&e=c6P2Ve",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOD19%202023F%20Syllabus.pdf?csf=1&web=1&e=c9CXab",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOD20H3%20Winter%202025%20Course%20Syllabus.pdf?csf=1&web=1&e=RikQlM",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOD20H3%20Winter%202024%20SYLLABUS.pdf?csf=1&web=1&e=VjAL4n",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOD21%20Course%20Syllabus%20-%20Summer%202025.pdf?csf=1&web=1&e=waQ3Ne",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD23%20Course%20Syllabus%20-%20Fall%202024.pdf?csf=1&web=1&e=3vjecT",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD21H3F-2024F%20Syllabus.pdf?csf=1&web=1&e=rgQcR0",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOD23%20Course%20Syllabus%20-%20Winter%202024.pdf?csf=1&web=1&e=NLrYsY",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOD24H3S-2025_Winter_Syllabus-20241217_KGan.pdf?csf=1&web=1&e=2KnRAr",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOD23H3%20Syllabus%20Sept%202023.pdf?csf=1&web=1&e=6pDaND",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOD21%20Course%20Syllabus%20-%20Summer%202024.pdf?csf=1&web=1&e=QZmce1",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOD25%20Syllabus%20Winter%202025.pdf?csf=1&web=1&e=RBP8Pj",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOD25%202024W%20Syllabus.pdf?csf=1&web=1&e=gPI1qh",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD26%202024F%20SYLLABUS.pdf?csf=1&web=1&e=C4eQMF",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD27%20-%20Course%20Syllabus%20-%20Fall%202024.docx.pdf?csf=1&web=1&e=lDeN0a",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOD29H%20Syllabus%20-Winter%202025_Final.pdf?csf=1&web=1&e=QpUphP",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOD26H3fall2023course%20outline.pdf?csf=1&web=1&e=w3ntvz",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOD29H%20Syllabus%20-Winter%202024%20(1).pdf?csf=1&web=1&e=fK6sBS",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD30H3F-2024_Fall_Syllabus.pdf?csf=1&web=1&e=B0C6hB",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Summer/BIOD32%20Summer%202025%20Syllabus.pdf?csf=1&web=1&e=3lKx6A",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2023%20Fall/BIOD30H3F-2023_Fall_Syllabus-20230826.pdf?csf=1&web=1&e=JTQfa3",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD32%20Fall%202024%20Syllabus%20(1).pdf?csf=1&web=1&e=8Daezg",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD37H3F-2024_Fall_Syllabus.pdf?csf=1&web=1&e=o5JSzL",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Summer/BIOD32H3Y%202024%20Summer_Syllabus%202024%2004%2029.pdf?csf=1&web=1&e=jzsJgh",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD34%20Course%20Syllabus%20Fall%202024.pdf?csf=1&web=1&e=eKSV4J",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOD43%20Winter%202025%20Syllabus%20-%202025Feb19.pdf?csf=1&web=1&e=G0niTb",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD45_syllabus2024b.pdf?csf=1&web=1&e=fvIP7T",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOD43%20Winter%202024%20Syllabus-Mar8Update.pdf?csf=1&web=1&e=PQfeiV",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD48H3F-2024_Fall_Syllabus.pdf?csf=1&web=1&e=DG57f8",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Winter/BIOD52%202024%20Syllabus.pdf?csf=1&web=1&e=ZW5IVd",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD60H3F-2024_Fall_Syllabus.pdf?csf=1&web=1&e=zommC9",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD59H3F-2024_Fall_Syllabus.pdf?csf=1&web=1&e=1405U3",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2025%20Winter/BIOD63H3%20Syllabus%20Winter%202025.pdf?csf=1&web=1&e=0etqbf",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    },
    {
      "url": "https://utoronto.sharepoint.com/:b:/r/sites/utsc-biologicalsciences/faculty-resources/Teaching%20Resources/Course%20Syllabi/Course%20Syllabi/2024%20Fall/BIOD65%202024F%20SYLLABUS.pdf?csf=1&web=1&e=3ltmFa",
      "source_url": "https://www.utsc.utoronto.ca/biosci/course-syllabi",
      "ok": false,
      "error": "HTTP Error 403: FORBIDDEN",
      "verified_at": "2026-10-14"
    }
  ]
}
```
