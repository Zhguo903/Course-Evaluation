# CourseInsight · 课程评价分析与选课推荐

[![Verify CourseInsight](https://github.com/Zhguo903/Course-Evaluation/actions/workflows/ci.yml/badge.svg)](https://github.com/Zhguo903/Course-Evaluation/actions/workflows/ci.yml)

将课程评分和文字评论转化为可比较的课程画像与选课建议。CourseInsight 串联 **数据清洗 → 分层数仓 → 文本标签 → 可解释推荐 → 交互式看板**，展示一个可在本地复现的数据工程与分析产品原型。

**数据说明：** 默认生成的课程、教师和评论均为虚构，未采集真实学生数据。GPA 友好度、职业相关性和推荐分是公开规则计算的辅助指标，不代表成绩预测、就业预测或已验证的推荐准确率。

## 快速开始

需要 Python 3.10+；GitHub Actions 在 Python 3.11 与 3.13 上运行检查。

```bash
git clone https://github.com/Zhguo903/Course-Evaluation.git
cd Course-Evaluation
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_pipeline.py
streamlit run app/streamlit_app.py
```

浏览器打开终端中显示的本地地址（通常为 `http://localhost:8501`）。首次打开时若尚未生成数据，也可点击看板中的初始化按钮。

默认数据规模：**200 门课程、60 位教师、8 个学期、800 条开课记录、12,000 条评论**。固定随机种子保证同一版本可复现；不同课程具有独立的评分、学习负担与内容特征。

## 能做什么

| 功能 | 使用方式与实现 |
| --- | --- |
| 课程探索 | 按院系、评分、工作量、难度和评论数量筛选，查看汇总指标 |
| 课程画像与比较 | 查看关键词、规则标签、评论样本，并比较多门课程 |
| 偏好推荐 | 根据高评分、低负担、项目实践等偏好调整排序，展示实际偏好分与推荐理由 |
| 相似课程 | 对课程名称、院系、标签、关键词建立 TF-IDF 向量，使用余弦相似度检索 |
| 数据质量 | 查看字段、日期、范围、主键、关联关系等检查的通过/失败及记录数量 |
| 结果导出 | 下载课程画像、推荐结果和质量报告的 CSV 文件 |

## v2 的改进

- **更可靠的数据处理：** 保留异常值供检查识别，避免把缺失字段转换为有效文本或把异常评分静默裁剪成合规数值。检查失败时阻止新的数仓发布，并保留诊断报告。
- **更稳健的推荐：** 用评论数量对课程均分进行平滑，排除已知无评论的课程；以确定性排序和与实际加减分对应的解释呈现推荐。
- **更有区分度的课程标签：** 根据评论提及比例与短语匹配打标签，处理简单否定，减少评论总量和宽泛词匹配的干扰。
- **更完整的交互：** 中文优先界面、筛选、课程对比、CSV 导出、缺失数据与空结果提示。
- **更易维护与复现：** 回归测试、Streamlit AppTest、GitHub Actions、独立开发依赖和指标文档。

## 数据流与仓库结构

```text
模拟数据生成 / 现有原始 CSV
            │
         pandas ETL
            │
      数据质量检查与门禁 ──失败──> 保存报告并终止
            │通过
       NLP 关键词与标签
            │
       DuckDB 本地数仓
   ODS → DWD → DWS → ADS
            │
   偏好推荐 / 相似课程检索
            │
     Streamlit + Plotly
```

| 层 | 作用 | 示例 |
| --- | --- | --- |
| ODS | 保留源数据形态，便于追溯 | `ods_reviews_raw` |
| DWD | 标准化明细与课程、教师、学期维度 | `dwd_reviews_clean` |
| DWS | SQL 汇总课程、教师、院系指标 | `dws_course_summary` |
| ADS | 课程画像、默认推荐排序、质量报告 | `ads_course_profile` |

仓库使用本地 DuckDB 文件。指标公式在 Python 与独立 SQL 示例中保持一致；推荐阶段合并课程标签，再根据当次勾选偏好计算 `preference_score`。详见 [指标定义](docs/metrics_definition.md)、[数仓设计](docs/warehouse_design.md) 和 [数据字典](docs/data_dictionary.md)。

## 推荐逻辑

1. 计算课程均分、难度、工作量、实用性与评论数。
2. 使用全局评论均分与 10 条先验评论平滑课程评分，减少极少量评价带来的波动。
3. 计算 1–5 范围内的课程画像分，再组合为默认 `recommend_score`。
4. 根据显式偏好加减分，得到最终排序用的 `preference_score`。该分数可能超过 5。
5. 返回与评分规则一致的理由；相似课程检索单独使用 TF-IDF 与余弦相似度。

没有用户行为训练、协同过滤或大语言模型调用；评论支持权重反映样本数量，**不表示预测准确率**。推荐方法及权重均可在 [src/recommender.py](src/recommender.py) 中审阅。

## 使用已有 CSV

将符合 [数据字典](docs/data_dictionary.md) 的五张源表放入 `data/raw/`：

```text
courses_raw.csv
instructors_raw.csv
semesters_raw.csv
course_offerings_raw.csv
reviews_raw.csv
```

```bash
python run_pipeline.py --skip-generate
```

该参数复用原始文件。默认 `python run_pipeline.py` 会重新生成模拟源数据。质量失败会返回非零退出状态，详情保存在 `data/processed/data_quality_report.csv`；修正源数据后再运行。已有 DuckDB 文件不会因门禁失败被覆盖。导入数据时，课程画像和质量报告均来自本地文件，不会上传至外部服务。

## 开发与验证

```bash
pip install -r requirements-dev.txt
ruff check .
pytest -q
python run_pipeline.py
```

测试覆盖数据清洗、完整性检查、异常阻断、评分平滑、标签/否定处理、排序解释、相似检索边界和看板交互。GitHub Actions 同时验证测试与完整数据流水线。

```text
app/                 Streamlit 看板
src/                 ETL、质量检查、标签、画像、推荐
sql/                 分层表与分析查询示例
docs/                指标、字典、设计、项目介绍与版本记录
tests/               单元与应用回归测试
run_pipeline.py      一键构建入口
```

## English overview

**CourseInsight is a local course-review analytics and explainable recommendation prototype.** Built with Python, pandas, DuckDB, scikit-learn, Streamlit and Plotly, it turns synthetic course reviews into a layered ODS–DWD–DWS–ADS warehouse, course profiles and interactive recommendations.

The default dataset contains 200 fictional courses, 60 instructors, 800 offerings and 12,000 reviews. The pipeline standardizes source data, validates integrity before publishing the warehouse, extracts TF-IDF keywords and proportion-based rule tags, and ranks courses using explicit preferences. Review-count smoothing limits the influence of sparse ratings. Similar courses are retrieved using TF-IDF cosine similarity.

The dashboard supports filtering, comparison, explanations, CSV exports and quality-report exploration. The project uses synthetic data and transparent heuristics; it does not claim measured improvements in student outcomes or recommendation accuracy.

## 后续方向

真实数据接入与隐私处理、基于真实反馈的离线评估、用户历史偏好、增量 ETL，以及数据量增长后引入调度与分布式计算。以上为后续方向，当前版本无需外部服务即可运行。
