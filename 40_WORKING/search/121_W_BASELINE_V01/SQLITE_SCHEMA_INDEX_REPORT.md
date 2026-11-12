# SQLite 스키마·인덱스

Python SQLite 및 CLI 3.54.0. 메모리 DB에서 FTS5 생성 성공. 운영 DB page_size=4096, page_count=21098, freelist_count=492, schema_version=1.

| 객체 | 구조 | 사용 공간 B |
|---|---|---:|
| docs | path TEXT PK, carrier/kind/sha/status/title/tags/content TEXT, sz/mtime_ns/scan INTEGER | 20402176 |
| sqlite_autoindex_docs_1 | path, BINARY 고유 B-tree | 876544 |
| manual | id TEXT PK, title/tags/path/source_grade/validation_grade/details TEXT | 4096 |
| sqlite_autoindex_manual_1 | id, BINARY 고유 B-tree | 4096 |
| ft | FTS5(path, tags, content), v1.1 DDL의 tokenizer trigram | shadow 합계 63111168 |
| sqlite_schema | 스키마 페이지 | 4096 |
| freelist | 492 페이지 | 2015232 |

FTS shadow 개별 bytes는 ft_config 4096, ft_content 19308544, ft_data 43544576, ft_docsize 77824, ft_idx 176128. 내부 인덱스 객체는 SQLite shadow PK에 포함된다. 별도 사용자 정의 인덱스, 뷰, 트리거는 운영 스키마에 없었다. 합계 86417408 B. FTS5 저장 공간은 약 73.0%이며 현행 query()의 SQL이 이 인덱스를 읽지 않는다. 이 인덱스의 보존·변경 판단에는 증분 쓰기와 기존 검색 동작 비교가 필요하다.
