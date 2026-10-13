# 指标定义 · v2

所有评分均来自合成数据。以下公开规则用于课程比较与推荐演示，不构成真实 GPA、就业结果或用户满意度预测。

## 基础指标与口径

| 字段 | 含义 |
| --- | --- |
| `review_count` | 有效评论记录数；无评论课程为 0 |
| `avg_rating` | 课程总体评分均值，1–5 |
| `avg_difficulty` | 难度均值，1–5，越大越难 |
| `avg_workload` | 工作量均值，1–5，越大负担越重 |
| `avg_usefulness` | 实用性均值，1–5 |
| `positive_review_ratio` | 评分 ≥ 4 的评论占比 |
| `negative_review_ratio` | 评分 ≤ 2 的评论占比 |

无评论课程的均分为 NULL，不能将其解释为零难度或零工作量。总体评分使用评论记录加权平均；不能简单平均各课程均分来替代。

## 评论数量平滑

设 `n = review_count`、`r = avg_rating`、`C = 全部有效评论的总体评分均值`、先验强度 `m = 10`：

```text
confidence      = n / (n + 10)
smoothed_rating = (n × r + 10 × C) / (n + 10)
```

`confidence` 表示课程自身评论在平滑均分中的权重（0–1），界面称“评论支持权重”。它不表示统计置信区间或预测准确率。没有评论的课程不参与推荐排序；低评论数课程的评分会向总体均值收缩。

## 课程画像分

各画像分统一为 1–5；越大表示该指标越强。`6 − x` 将负向指标转换为同一范围内的正向指标。

```text
gpa_friendly_score = 0.4 × smoothed_rating
                   + 0.3 × (6 − avg_difficulty)
                   + 0.3 × (6 − avg_workload)

course_value_score = 0.6 × avg_usefulness
                   + 0.4 × (6 − avg_workload)

data_career_relevance_score = min(5, department_base + 2 × data_keyword_ratio)

workload_risk_score = 0.6 × avg_workload
                    + 0.4 × (1 + 4 × workload_negative_ratio)
```

- `gpa_friendly_score`：高评分、低难度、低工作量的组合；没有真实成绩数据，不能等同于“容易得高分”。
- `course_value_score`：实用性与工作量的折中；v2 使用统一量纲的加权分，替代旧版比值。
- `data_career_relevance_score`：数据科学、计算机、统计院系的基础分为 3.5，其余为 2.0，再结合相关短语的评论提及比例。
- `workload_risk_score`：工作量与负担相关短语提及比例；越大表示负担越重。

提及比例按每条非空评论是否出现相关短语计数，同一评论重复出现同一短语不会重复加权。词语采用边界匹配与简单否定处理；规则与词表见 `src/nlp_tags.py`。

## 默认推荐分与当次偏好分

```text
recommend_score = 0.25 × smoothed_rating
                + 0.20 × gpa_friendly_score
                + 0.20 × data_career_relevance_score
                + 0.15 × course_value_score
                + 0.10 × avg_usefulness
                + 0.10 × (6 − avg_workload)
```

`recommend_score` 为默认画像分。`preference_score` 在此基础上叠加当次显式偏好，最终结果按后者排序；它不限定在 1–5，也不是推荐概率。具体偏好权重与解释见 `src/recommender.py`。

## 标签与文本相似度

TF-IDF 从按课程合并的英文评论中提取关键词。内容标签按评论提及比例生成，默认比例阈值为 30%，评分型标签另有均分条件。词典情感是轻量规则方法，无法充分理解讽刺或复杂否定。

相似检索将课程名称、院系、标签和关键词组合成文本，使用 TF-IDF 向量的余弦相似度（0–1）。零相似度结果不返回；同分时使用稳定次序。相似度表示内容接近程度，不表示课程优劣。

## 可复现依据

ADS 指标的单一定义位于 `sql/04_create_ads_tables.sql`，数仓构建与 CSV 回退路径均执行相同 SQL。修改指标时应同步本文、SQL 示例和回归测试；数据生成逻辑改变后需要重新运行 `python run_pipeline.py`。
