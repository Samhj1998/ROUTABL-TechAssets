# A/B/C 최종 판정표

| 후보 | 기능 | 성능 | 운영 채택 판단 |
|---|---|---|---|
| A | 기준선 및 회귀 대조 PASS | 비교 기준 | 현행 유지 권고 |
| B | PASS | 기준 미달 | 보류 |
| C | PASS | 기준 미달 | 보류 |

| 규모 | 연결 | B 혼합/선택적 | C 혼합/선택적 |
|---|---|---|---|
| 1x | reuse | PASS / PASS | PASS / PASS |
| 1x | fresh | 기준 미달 / 기준 미달 | 기준 미달 / 기준 미달 |
| 5x | reuse | PASS / PASS | PASS / PASS |
| 5x | fresh | 기준 미달 / 기준 미달 | 기준 미달 / 기준 미달 |
| 10x | reuse | PASS / PASS | PASS / PASS |
| 10x | fresh | 기준 미달 / 기준 미달 | 기준 미달 / 기준 미달 |

| 1배 보조 유형 | 연결 | B (악화 10% 이내) | C (악화 10% 이내) |
|---|---|---|---|
| PERF-DENSE-1X | reuse | 기준 미달 | 기준 미달 |
| PERF-DENSE-1X | fresh | 기준 미달 | 기준 미달 |
| PERF-SHORT-1X | reuse | PASS | PASS |
| PERF-SHORT-1X | fresh | 기준 미달 | PASS |
| PERF-ALIAS-SHORT-1X | reuse | PASS | PASS |
| PERF-ALIAS-SHORT-1X | fresh | 기준 미달 | PASS |
| PERF-NUL-1X | reuse | PASS | PASS |
| PERF-NUL-1X | fresh | 기준 미달 | PASS |
| FAULT-FT-MISSING | reuse | PASS | PASS |
| FAULT-FT-MISSING | fresh | 기준 미달 | 기준 미달 |
| FAULT-FT-DDL | reuse | PASS | PASS |
| FAULT-FT-DDL | fresh | PASS | PASS |
| FAULT-MATCH | reuse | 기준 미달 | PASS |

| 배수 | 색인 전체 생성 +10% 이내 B/C | 증분 각 +10% 이내 B/C | 저장 +5% 이내 B/C |
|---|---|---|---|
| 1x | 기준 미달 / 기준 미달 | 기준 미달 / 기준 미달 | PASS / PASS |
| 5x | 기준 미달 / 기준 미달 | 기준 미달 / 기준 미달 | PASS / PASS |
| 10x | 기준 미달 / 기준 미달 | 기준 미달 / 기준 미달 | PASS / PASS |

판단 근거는 운영과 유사한 새 연결의 검증비용과 보조 질의, 색인 수명주기다. 재사용 연결의 선택적 검색 편익은 격리 계측에서 관측됐다. 채택 판단은 121 Chat에 남긴다. 후속 D 연구를 택할 경우 세대 검증을 갱신 시점으로 옮기고 짧은·다건에서 A 경로로 분기하는 별도 판본 및 통합 시험을 검토할 수 있다.
