# 공통 분석 입력 후보 v0.1

M01. 현재 문서 질의는 별칭을 확장하고 각 용어별 path/title/tags/content 리터럴 포함 조건을 OR로 적용한다. manual은 별도 Python 문자열 매칭. 범위 필터는 Python 단계에 있다. 입력 길이 2~80, 범위 all/main/variants/nas.

M02. SQLite 3.54.0. docs(path PK, carrier, kind, sz, mtime_ns, sha, status, title, tags, content, scan). manual(id PK, title, tags, path, source_grade, validation_grade, details). FTS5 trigram ft(path,tags,content). B-tree PK는 등호의 경우 사용. 실제 문서 LIKE 및 manual 계획은 SCAN. FTS MATCH 대조는 VIRTUAL TABLE INDEX.

M03. 파일명 exact/prefix/infix 125/94/68, 제목 exact/prefix/infix 64/46/33, 경로/태그 18/13. 별칭 0.65 가중치. 범주·테스트 경로·일부 버전명·상태·경로와 SHA가 일치하는 provenance의 보정이 있다. 스코어 내림차순, 경로 오름차순. SHA 길이 64인 경우 동일 해시 묶기, 그 외 path 기준. 결과 페이지는 그룹화 후. 그룹 위치 최대 25개. 일반 최신 판본 자동 승격이나 초성 전처리는 현행 규칙에 없다.

M04. 평가자에게만 실제 회귀 문자열을 제공한다. 다음은 기존 9건의 검색 범위와 기대 match/group/manual 집계다.

| ID | 유형 | 범위 | match/group/manual |
|---|---|---|---|
| R01 | 설정 별칭 | all | 89/57/1 |
| R02 | 설정 별칭 | all | 121/47/2 |
| R03 | 설정 별칭 | all | 87/31/0 |
| R04 | 설정 별칭 | main | 574/542/1 |
| R05 | 기타 | main | 3/1/1 |
| R06 | 기타 | main | 4/1/1 |
| R07 | 기타 | variants | 0/0/0 |
| R08 | 기타 | nas | 1776/1422/1 |
| R09 | 기타 | all | 0/0/0 |

M05. 순수 합성 corpus와 개발 질의 30건은 별도 JSON. 보류 20건은 평가자 전용.

M06. 평가 규격은 COMMON_TEST_SPEC.md. 각 AI는 변경 내용, 가설, 호환성 위험, 안전한 검증 경로를 독립적으로 제안한다.
