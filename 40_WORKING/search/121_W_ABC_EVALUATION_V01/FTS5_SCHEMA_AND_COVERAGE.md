# FTS5 실제 스키마와 후보 포괄성

Mac Studio arm64, macOS 27.2, Python 3.9.6, SQLite 3.54.0. 운영 원본은 `mode=ro` + `query_only=ON`으로 연결했다. SQLite Backup API로 평가 전용 사본을 만들고, `quick_check`, FTS integrity-check와 데이터 집계를 사본에서 수행했다. 원본 SHA-256 및 -wal/-shm/-journal 부재를 전후 확인했다. 원본 운영 행, 검색어, 실제 경로 결과를 출력하지 않았다.

```sql
CREATE VIRTUAL TABLE ft USING fts5(path,tags,content,tokenize='trigram')
```

- 일반 내부 콘텐츠 FTS5다. `ft_content` 등 shadow 테이블이 있으며 external content 및 contentless 옵션이 없다. `path`, `tags`, `content` 모두 색인 대상이다. `title` 열은 별도로 존재하지 않는다.
- `case_sensitive=0`, `remove_diacritics=0`, `detail=full`은 DDL 생략에 따른 기본값이다. 설치본에서 기본/민감도/none/column 변형을 같은 테스트로 대조했다.
- docs와 ft는 현재 세대의 `rowid`로 대응한다. docs/ft 각 5,519행, manual 3행. 빠진 rowid·고아 rowid·tags/content 불일치 각 0건. 모든 행의 `ft.path`가 `docs.path || ' ' || docs.title`이었다. raw path 일치 0행. 운영 데이터가 포함된 사본은 평가자 전용이다.
- docs path는 고유 B-tree이지만 선행 %와 ESCAPE가 있는 부분 문자열 조회는 SCAN이었다. FTS5 가상 테이블의 MATCH는 인덱스 계획을 썼다. FTS에 LIKE만 썼을 때 `L0`, ESCAPE를 붙이면 `L0`가 없어짐을 변형 표본에서 확인했다.
- 전체 DB 86,417,408 B. FTS shadow 합계 63,111,168 B. 이번 단계에 추가한 운영 인덱스는 없다.

| 설치본 합성 대조 | LIKE | literal MATCH 또는 합집합 | 판정 |
|---|---:|---:|---|
| 2자 한글 | 2 | 0 | FAIL. 이 경로를 강제하면 누락 |
| 3자 한글 및 별도 4자 이상 한글 | 각각 1 | 각각 1 | 표본 PASS |
| 2자 별칭이 포함된 OR 질의 | 2 | 0 | FAIL. 짧은 확장어 하나라도 있으면 질의 전체 폴백이 필요 |
| 제목 전용 | 1 | MATCH 1, 제목 분기 1 | 합성 path+title 색인에서 관측. 원래 제목 조건은 유지 |
| 경로 전용 / 태그 전용 / 본문 전용 | 각 1 | 각 1 | rowid 후보 표본 PASS |
| ASCII case / 인용부호 / 공백 / 하이픈 / MATCH 연산자 문자열 | 각 1 | 각 1 | 리터럴 인용과 바인딩 표본 PASS |
| 리터럴 %, _, ! | 2 | 2 | ESCAPE 판정 재사용 표본 PASS |
| Unicode 대소문자 | 1 | 2 | 과다 후보 1건. A 조건 재검사 필요 |
| NFC·NFD 각각, 자모 리터럴, 이모지 포함 | 각각 1 | 각각 1 | 문자열 포함 표본 PASS. 초성 변환 기능은 별개 |
| NUL이 섞인 MATCH 입력 2종 | A 의미 보존 대상 | 파싱 오류 2종 | MATCH 금지 또는 실패 시 A로 복귀 |
| `detail=column`, `detail=none` | — | 3자 1행, 4자 이상 phrase 오류 | 해당 옵션을 가속 허용 대상으로 가정하면 FAIL |
| `case_sensitive=1`과 ASCII 소문자 | 1 | 0 | 현재 DDL은 기본값. 옵션 변화는 세대 검증·폴백 대상 |

합성 개발 30질의에서 A의 네 컬럼 LIKE를 기대 집합으로 비교했다. 원문·합성 별칭을 적용한 `rowid` 합집합 누락은 0, `ft.path`와 docs.path를 직접 조인한 합집합은 54개의 질의·행 쌍을 놓쳤다. 운영 회귀 9건의 후보별 비교, 보류 20건, 모든 유효 문자열의 포괄성 증명은 NOT_TESTED다. 색인 컬럼이 접합한 경로·제목 경계에서 생긴 후보도 원본 A 조건으로 제거해야 한다.

공식 문서는 3 Unicode 문자 미만의 MATCH 제한, detail 모드, case와 LIKE ESCAPE를 설명한다. 실제 결과는 `FTS5_MEASURED_EVIDENCE.json`의 variants·edge·dev를 기준으로 한다. [SQLite FTS5](https://sqlite.org/fts5.html#the_trigram_tokenizer) · [SQLite Backup API](https://sqlite.org/backup.html)
