# St. George 公开学习资料扩充

核验日期：2026-10-14（America/Toronto）。最终冻结 81 条链接元数据，精确关联 69 门当前 St. George 课程。

仅保存原站链接与事实性元数据，没有镜像大纲、题目、答案、课件或教材全文。每个课程/来源仅选择少量代表入口，完整练习集合由原站目录提供。

## 资源类型

- course_materials: 15
- practice_exam: 3
- practice_problems: 4
- syllabus: 59

其中 7 条练习/模拟试卷、15 条课程资料入口均关联具体课程，不是通用导航链接。首轮 67 条中的 5 条练习和 7 条课程资料同样均为实际课程关联；追加 5 门数学课程及已核验的统计学规范域名入口后，最终为 81 条 / 69 门。

## 核验方式

官方索引或课程页提供代码、期次和真实 href；逐个 GET 核验 HTTP 200、HTTPS 官方域及可读 HTML/PDF。PDF 仅在内存检查前两页后释放，不保留原文件或摘录。当前 load_catalog 精确校验 St. George 完整代码，不跨校区、不替换 H/Y。期次未明时保留为空。课程页注明的学期不自动继承给旧试卷；代表文件另行核验自身代码、校区和期次。

CS 大纲索引要求仅供参考、不要分发或再利用大纲内信息。本集合仅索引课程代码、期次和原站链接，不复制大纲内容；原站条件仍适用。公开访问仅表示核验时无需登录，不表示原内容可自由转载。

脚本使用核验当天的 Toronto 日期，拒绝指定其他日期；旧页面的教学期次独立记录，不将核验日期当作课程资料年份。复核不会跟随成绩表、学生信息、登录系统或教材下载链接。

## 已核验来源列表

- https://utstat.utoronto.ca/sjaimung/courses/sta2502/2010/main.htm
- https://www.math.toronto.edu/mpugh/Teaching/APM236_04/handout.html
- https://web.cs.toronto.edu/undergraduate/courses/outlines
- https://www.math.toronto.edu/nhoell/MAT224/
- https://www.math.toronto.edu/courses/mat237y1/20199/
- https://www.math.toronto.edu/courses/mat244h1/20189/
- https://www.math.toronto.edu/campesat/mat246.html
- https://www.math.toronto.edu/vtk/247Winter2012/
- https://www.math.toronto.edu/~vtk/257Fall09/
- https://www.math.toronto.edu/balazse/2019_Fall_MAT344/index.html
- https://www.math.toronto.edu/herzig/347-f26.html
- https://www.math.toronto.edu/alfonso/347/347_Test1.html
- https://www.math.toronto.edu/nhoell/MAT354.html
- https://www.math.toronto.edu/~rafi/MAT475.html
- https://utstat.toronto.edu/alisong/Teaching/Fall03/sta302.html
- https://utstat.toronto.edu/alisong/Teaching/Fall03/Sta302/pp.html
- https://utstat.utoronto.ca/alisong/Teaching/1112/Sta303/sta303.html
- https://utstat.toronto.edu/reid/442F10.html

## 排除与失败检查

以下链接未计入资源。失败不推断资源永久不存在。TLS 验证保持启用；原 www.utstat 主机证书不匹配，后来仅对另行读取并核验成功的官方规范域名收录，原失败记录保留。
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Fall/CSC110H1F-Fall2025.pdf — Official index code CSC110H1 absent from current SG catalog; no H/Y substitution.
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2026/Winter/CSC301H1S-Winter2026.pdf — PDF content did not identify the indexed course
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Fall/CSC320H1F-Fall2025.pdf — The read operation timed out
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Winter/CSC320H1S-Winter2025.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2024/Fall/CSC320H1F-Fall2024.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2024/Winter/CSC320H1-Winter2024.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Fall/CSC324H1F-Fall2025.pdf — The read operation timed out
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2024/Fall/CSC324H1F-Fall2024.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2024/Winter/CSC324H1-Winter2024.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Fall/CSC336H1F-Fall2025.pdf — The read operation timed out
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Winter/CSC336H1-Winter2025.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2024/Winter/CSC336H1-Winter2024.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2023/Fall/CSC336H1-Fall2023.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2026/Winter/CSC343H1S-Winter2026.pdf — <urlopen error [Errno 60] Operation timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Fall/CSC343H1F-Fall2025.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Winter/CSC343H1S-Winter2025.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2024/Fall/CSC343H1F-Fall2024.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2024/Winter/CSC343H1-Winter2024.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2023/Fall/CSC343H1-Fall2023.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Fall/CSC364H1F-Fall2025.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2026/Winter/CSC367H1S-Winter2026.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Fall/CSC368H1F-Fall2025.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2026/Winter/CSC369H1S-Winter2026.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2026/Winter/CSC373H1S-Winter2026.pdf — PDF first pages have no readable verification text
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2026/Winter/CSC488H1S-Winter2026.pdf — PDF content did not identify the indexed course
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Winter/CSC488H1S-Winter2025.pdf — <urlopen error [Errno 60] Operation timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2024/Winter/CSC488H1-Winter2024.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2026/Winter/CSC491H1S-Winter2026.pdf — <urlopen error _ssl.c:993: The handshake operation timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Fall/CSC491H1F-Fall2025.pdf — <urlopen error timed out>
- https://www.cs.toronto.edu/dcs/ugdocs/course-outlines/2025/Winter/CSC491H1S-Winter2025.pdf — <urlopen error timed out>
- https://www.math.toronto.edu/~vtk/257Fall09/final-past-sol-257.pdf — child content does not independently identify course
- https://www.math.toronto.edu/nhoell/MAT354_syllabus.pdf — HTTP Error 404: Not Found
- https://www.cs.toronto.edu/~rahulgk/courses/csc311_f24/index.html — <urlopen error timed out>
- https://www.cs.toronto.edu/~rahulgk/courses/csc311_f23/index.html — <urlopen error timed out>
- https://www.cs.toronto.edu/~toni/Courses/263-2013/263.html — <urlopen error timed out>
- https://www.cs.toronto.edu/~krueger/csc363h/tests/ — CSC363H1 absent from current SG catalog
- https://www.cs.toronto.edu/~krueger/csc373h/tests/ — <urlopen error timed out>
- https://www.cs.toronto.edu/~krueger/csc165h/tests/ — <urlopen error timed out>
- https://www.cs.toronto.edu/~raeidsaqur/csc401/ — <urlopen error timed out>
- https://www.cs.toronto.edu/~fidler/teaching/2024/CSC420.html — <urlopen error timed out>
- https://www.utstat.toronto.edu/alisong/Teaching/Fall03/sta302.html — <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.utstat.toronto.edu'. (_ssl.c:1010)>
- https://www.utstat.toronto.edu/alisong/Teaching/1112/Sta303/sta303.html — <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.utstat.toronto.edu'. (_ssl.c:1010)>
- https://utstat.toronto.edu/reid/sta442f/PracticeQuestions.pdf — HTTP Error 404: Not Found
- https://www.utstat.toronto.edu/sjaimung/courses/sta2502/2010/main.htm — <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.utstat.toronto.edu'. (_ssl.c:1010)>
- https://www.math.toronto.edu/nhoell/MAT224/Practice_Final.pdf — child content does not independently identify course
- https://www.math.toronto.edu/nhoell/MAT224/Practice_test2.pdf — child content does not independently identify course
- https://www.math.toronto.edu/nhoell/MAT224/Practice_test1.pdf — child content does not independently identify course
- https://www.math.toronto.edu/vtk/247Winter2012/247practicefinalsol.pdf — child content does not independently identify course
- https://www.math.toronto.edu/vtk/247Winter2012/247practicefinal.pdf — child content does not independently identify course

MAT257 历史 final 无法从文件自身确认课程身份，已排除；不以父页面链接代替这一检查。明确不将旧 MAT137Y1、MAT235Y1、MAT135Y1、STA107 或 STA260 资料改配到代码相似的当前或外校区课程。
