# Metrics Definition

## Core Review Metrics

| Metric | Definition |
| --- | --- |
| avg_rating | Average overall rating for a course, instructor, or department |
| avg_difficulty | Average difficulty score |
| avg_workload | Average workload score |
| avg_usefulness | Average usefulness score |

## ADS Course Profile Scores

### gpa_friendly_score

```text
0.4 * avg_rating + 0.3 * (5 - avg_difficulty) + 0.3 * (5 - avg_workload)
```

Higher values indicate courses that combine strong ratings with lower difficulty and workload.

### course_value_score

```text
avg_usefulness / NULLIF(avg_workload, 0)
```

Higher values indicate strong usefulness relative to workload.

### data_career_relevance_score

Departments in Data Science, Computer Science, and Statistics receive a higher base score. Reviews containing data-career keywords such as python, sql, data, machine learning, visualization, and project add relevance.

### workload_risk_score

```text
0.6 * avg_workload + 0.4 * workload_negative_ratio
```

Higher values indicate heavier workload risk.

### recommend_score

```text
0.25 * avg_rating
+ 0.20 * gpa_friendly_score
+ 0.20 * data_career_relevance_score
+ 0.15 * course_value_score
+ 0.10 * avg_usefulness
+ 0.10 * (5 - avg_workload)
```

This is the default global ranking score before user-specific preferences are applied.
