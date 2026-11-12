# FTS5 격리 실현 가능성

## 스냅샷과 갱신

- **PASS**. 평가용 운영 DB SQLite Backup API 사본, 스냅샷 86,417,408 B, SHA-256 `c7fc620620e87f885b506f72c14fcd68644a381dae58d8c1acf5b976e1359f22`. 운영 DB의 해시와 별개로 관리한다. 사본의 quick_check, native FTS integrity-check, docs/ft rowid 및 필드 정합성 검사를 통과했다.
- **PASS**. 격리 합성 DB에서 고정된 v1.1 `setup/add`와 v1.1 stale 삭제 SQL을 그대로 사용했다. 삽입/읽기, 변경 mtime 갱신, 이전 문구 제거, 삭제·이름 변경, 트랜잭션 롤백을 관측했다. 이 삭제 SQL은 v1.1의 전체 스캔 경로 근거다.
- **FAIL 반례**. 동일 경로의 크기·mtime을 유지한 채 내용을 바꾸면 v1.1 add 단독 경로는 이전 텍스트를 남겼다. 새 이름 add만 호출하면 기존 이름도 남았다. native FTS integrity-check만으로는 일부 docs가 FTS에서 누락된 상태를 탐지하지 못했다. 문서/FTS 전수 교차검사 및 색인 세대 검증을 게이트로 둔다.
- **PASS**. 운영이 위임하는 v1.4 `refresh_worker/check_db` 및 v1.3 `build` 함수 본문을 보존해 합성 파일만 바라보도록 주입했다. 기존 2,272개 합성 seed 중 보호 2개를 둔 고정 베이스에서 네 세대를 시험했다. 추가, 같은 size/mtime의 수정, 이름 변경, 삭제가 반영됐고 모든 세대에 docs/ft 행 정합성 위반·고아 0건이었다. v1.3은 **고정 PREVIOUS DB를 다시 복제**해 허용 목록을 재구축한다. v1.1 add의 무변경 단축을 그대로 연속 활성 DB에 적용한 경우와 구별한다.
- **제약**. 위 refresh에서 synthetic classifier·태그·경로·로더를 주입했다. 실제 파일 분류, 운영 HTTP 서비스의 동시 독자, 장애 복구 동작, 배포 중 롤백 실행은 NOT_TESTED. 롤백 파일의 이전 행 수는 확인했으나 백업 파일의 물리 SHA는 기존 파일 SHA와 달랐고 전체 논리 동등성까지 비교하지 않았다. 향후 복구는 행·스키마·결과 계약으로 검증한다.

## SQL 비용 대조

1,230행 합성 fixture, arm64 macOS 27.2, Python 3.9.6, SQLite 3.54.0. 새 DB 또는 강제 cold-cache가 아닌 재사용 연결이다. 각 문장은 30회 실행했고 p95는 nearest-rank다. 구성요소 측정은 순서를 교차했다. 아래 recheck-only는 MATCH로 미리 얻은 rowid를 바인딩하고 fetch한 시간이다.

| SQL 구성요소 | 선택적 본문 3행 p95 ms | SIM 30행 p95 ms |
|---|---:|---:|
| A의 4컬럼 LIKE rowid 조회 | 3.3952 | 2.9025 |
| MATCH rowid 조회 | 0.2361 | 0.1518 |
| 제목 LIKE 단독 SCAN | 0.7477 | 0.5919 |
| MATCH rowid에 한정해 A 조건 재검사 | 0.2942 | 0.3043 |

별도 메모리 사본에서 SQL 형태를 대조했다. 일치 3행 표본에서 A LIKE 2.9182ms, `rowid UNION + 원본 LIKE` 0.4933ms. 일치 1,200행 표본에서 A LIKE 2.0986ms, 같은 합집합/재검사 3.6045ms. content까지 가져오는 넓은 UNION 형태는 1,200행에서 6.8231ms였고 반환 열이 다르므로 직접적인 동등 성능 비교에는 쓰지 않는다. 실측 계획은 MERGE(UNION)이었다. 제목 커버링 B-tree를 합성 메모리 사본에만 만들어 보니 제목 계획은 여전히 SCAN이며 커버링 스캔을 사용했다. 해당 인덱스는 73,728 B이고 단일 선택적 대조 p95 0.2802ms였다. 운영 저장 공간·갱신 비용이나 최종 후보 채택을 추정하는 수치로 사용하지 않는다.

**판정**. 검증된 DDL·행 연결과 짧은 용어/FTS 오류의 전체 폴백 조건으로 FTS 후보 축소를 후속 구현 시험에 올릴 수 있다. 선택적/다건의 방향 차이를 확인했다. 이 단계에서 계측한 것은 SQL 단계이며 API 전체 응답, Python 후처리, 최종 정확도, 인덱스 갱신 시간, 저장 한도, 운영 회귀의 B/C 합격은 NOT_TESTED다.

근거 `FTS5_FEASIBILITY_PROBE.py`, `FTS5_MEASURED_EVIDENCE.json`, `FTS5_REFRESH_AND_PACKET_PROBE.py`, `FTS5_REFRESH_AND_PACKET_EVIDENCE.json`, `FTS5_SQL_SHAPE_EVIDENCE.json`. [SQLite FTS5 integrity-check](https://sqlite.org/fts5.html#the_integrity_check_command)
