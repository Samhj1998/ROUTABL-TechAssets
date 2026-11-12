# 읽기 전용 SQLite 실행계획

`docs` 조회에서 후보 조건은 각 검색어와 별칭마다 `path/title/tags/content LIKE ? ESCAPE '!'` 네 항을 OR로 결합한다. 바인딩에는 양끝 %가 붙고 리터럴 %, _, !를 이스케이프한다. 전체 manual 읽기는 WHERE 조건 없이 수행한다.

| 계획 | 출력 |
|---|---|
| 실제 docs SQL · 바인딩 4, 8, 12개 | SCAN docs |
| 실제 manual SQL | SCAN manual |
| 대조 · docs.path = ? | SEARCH docs USING COVERING INDEX sqlite_autoindex_docs_1 (path=?) |
| 대조 · manual.id = ? | SEARCH manual USING COVERING INDEX sqlite_autoindex_manual_1 (id=?) |
| 대조 · ft MATCH ? | SCAN ft VIRTUAL TABLE INDEX 0:M3 |

FTS 대조는 MATCH를 사용한 가상테이블 계획이다. 개선 후보 실행이나 FTS 지연 측정은 수행하지 않았다. 기존 쿼리에서 앞쪽 %를 갖는 부분 문자열과 OR 때문에 일반 path PK를 타는 계획이 확인되지 않았다. 점수·정렬·중복·페이지 처리는 DB 밖에서 실행한다. 원시 근거는 BASELINE_MEASURED_EVIDENCE.txt.
