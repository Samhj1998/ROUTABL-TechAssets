# 기준선 원본 및 고정 증거

점검 시각 2026-11-08 09:31 이후 KST. MacStudioui-MacStudio.local · c377300b-a710-43a6-8169-f17e87175403. Python 3.9.6, CLI/Python SQLite 3.54.0.

S는 /Users/yongho/Library/Application Support/ROUTABL-AssetSearch. E는 /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01.

| 파일 | 바이트 | SHA-256 |
|---|---:|---|
| S/routabl_search_v1_5_service.py · ASSET-SEARCH-01 v1.5 | 22823 | 55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d |
| S/assets_v1_5.sqlite · 운영 검색 DB | 86417408 | c5a800f36aaaeddd1b5aad086403df115fa8f99fb8f616271421e89dff71cba4 |
| E/FIRST_IGNITION_CLOSEOUT_REPORT.md | 4509 | 2b893b170bd2a2a4b13f45bf82b1a929d7481e9f5d657a7ebfecb17e1525dd36 |
| E/SHA256SUMS | 2364 | 2d0f11da7a99302c32cced5f35e753e885b30db1cb75bd1e9a57fb27d92434b8 |
| E/SEARCH_REGRESSION.json | 6844 | 6c2f0486b4ecc33aecde4156edbc2fe8f9b06cb717b937e60bdee3b9ea1a8cbf |
| E/assets_v1_5.sqlite · 보존 비교 DB | 86417408 | dc72ddd7561b5a882dfb49f2865098bde435dc1c04352c6cd3dbbd699368d0bf |
| E/routabl_search_v1_5_service.py · 보존 증거의 별도 소스 | 9377 | f391044addc200f7c2cd70cb68163e913751c619b5a9b8ff42afc824e08885fc |

서비스 코드의 INDEX가 S/assets_v1_5.sqlite를 가리킨다. 지정 포트 8769의 리스너는 점검 순간에 관측되지 않았다. 실제 HTTP 동작은 NOT_TESTED이며 서비스 실행 또는 재시작을 요청하지 않았다. 검색 함수와 SQLite의 실제 연결 관계는 해시 고정 함수 계측으로 확인했다. DB는 rollback journal 헤더와 journal_mode=delete, 부속 WAL/SHM/journal 부재 확인 후 mode=ro로 접근했다. 시험 전후 inode·크기·mtime·ctime이 일치했다. 두 DB는 SHA가 다르며 회귀 비교 결과는 지정 질의 9건의 범위다.
