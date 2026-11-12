# 기능 회귀 결과

| 데이터 | A 기준 B 전체 객체 일치 | A 기준 C 전체 객체 일치 |
|---|---:|---:|
| 운영 고정 9질의 | 9/9 PASS | 9/9 PASS |
| 1배 공개 개발 | 30/30 PASS | 30/30 PASS |
| 1배 보류 | 20/20 PASS | 20/20 PASS |
| 5배 공개/보류 | 30/30 · 20/20 PASS | 30/30 · 20/20 PASS |
| 10배 공개/보류 | 30/30 · 20/20 PASS | 30/30 · 20/20 PASS |

운영 9건의 A match/group/manual 개수도 과거 기록 9/9와 일치했다. 비교는 일부 필드 추출 대신 반환 dict 전체의 동등성으로 수행했다. 반환 순서·점수·scope·페이지·상태·대표·SHA·위치·manual·검증 링크 마스킹이 결과에 포함된다.

동일 qrels v01, 그룹 중복 0점, 질의별 macro 평균. 세 규모의 A/B/C 공개 및 보류 점수는 각각 Recall@10 0.800, Precision@10 0.160, MRR@10 0.800, nDCG@10 0.800. 대표·SHA·상태·버전·중복 위치 모두 공개 24/30, 보류 16/20. 현행 A와 동일한 초성 기대 미충족 공개 6건·보류 4건은 절대 점수에 포함했으며 속도 최적화의 새 회귀는 0건이다.

증거 `ACCURACY_COMPARISON.csv`, `private/functional.json`, `private/operating_historical_counts.json`, `private/functional_addendum.json`.
