# 120. 라우터블 기술자산 통합검색 v1.7 — Mac에서 사용하기 + Claude 제어

작성: 2026-11-12 | 대상: Mac Studio | v1.6(8770)·v1.5 보존, 건드리지 않음

## 처음 한 번
- `~/Applications/라우터블 기술자산 검색 v1.7.app` 더블클릭 → `http://127.0.0.1:8771/`
- 첫 실행에서 하는 일
  1. `40_WORKING/SEARCH_V1_7_20261112/v1_7/`의 서비스·스캐너를 `~/Library/Application Support/ROUTABL-AssetSearch/`에 설치 (바뀐 경우만, v1.6 파일은 그대로)
  2. LaunchAgent `com.routabl.assetsearch.v17` 등록 → 로그인할 때마다 자동으로 켜짐, 쉬어도 꺼지지 않음 (127.0.0.1 전용)
  3. 첫 화면은 NAS 기준선(2,272행)만 있음 → **검색 목록 새로 고침** 한 번 (시험 환경 결과 3,841행)
- 끄기(해제): 터미널에서 `launchctl bootout gui/$(id -u)/com.routabl.assetsearch.v17` 후 `~/Library/LaunchAgents/com.routabl.assetsearch.v17.plist` 삭제

## v1.6과 달라진 점
- 검색 대상에 **고객등록앱** `ROUTABL-CustomerRegistration-Android` 추가 (별명: 고객등록앱, 행정동)
- 같은 파일이 여러 번 등록되어 있으면 **지금 파일과 SHA가 같은 등록**의 자산 ID를 표시 (v1.6은 첫 등록만 써서 재등록 자산이 가려짐)
- 서비스가 켜진 채로 새 등록부(asset_manifest_v0.N)가 생기면 다음 검색 때 자동으로 다시 읽음
- 쉬어도 꺼지지 않음 (v1.6은 45분 쉬면 꺼져서 Claude가 접속할 수 없었음)
- 새 읽기 전용 API `/api/registry`

## Claude가 직접 쓰는 방법 (내장 브라우저)
| 하려는 일 | 방법 |
|---|---|
| 상태 확인 | `http://127.0.0.1:8771/api/status` 열기 |
| 검색 (JSON) | `http://127.0.0.1:8771/api?q=검색어&scope=all` (scope: all·main·docs·variants·nas) |
| 등록부 점검 | `http://127.0.0.1:8771/api/registry` → matched / superseded(재등록으로 대체됨) / stale(파일이 바뀌었는데 재등록 안 됨) / not_indexed(검색 범위 밖) |
| 새로 고침 | `http://127.0.0.1:8771/` 화면의 **검색 목록 새로 고침** 버튼 클릭 (변경 요청은 화면 토큰이 필요 — 바깥 웹페이지가 대신 누를 수 없게) |

- 자산 등록 후 점검 순서: 새 `asset_manifest_v0.N.json` 작성 → 새로 고침 → `/api/registry`의 `stale`이 0인지 확인
- 서비스가 응답하지 않으면: 사용자에게 v1.7 앱 더블클릭 요청 (Claude는 `~/Library`에 쓸 수 없고, 원격 셸은 Mac 명령을 실행하지 못함)

## 파일
- 원본(작업): `40_WORKING/SEARCH_V1_7_20261112/v1_7/routabl_search_v1_7_service.py`, `routabl_assetsearch_v1_7_scanner.py`
- 앱 원본: `40_WORKING/SEARCH_V1_7_20261112/app_bundle_v1_7/`
- 설치 위치: `~/Library/Application Support/ROUTABL-AssetSearch/` — 색인 `assets_v1_7.sqlite` / 직전 `assets_v1_7.previous.sqlite` / 로그 `search_v1_7_service.log`, `search_v1_7_launcher.log`

## 알아둘 점
- v1.6과 마찬가지로 같은 폴더의 `routabl_search_v1_4_service.py`(공통 엔진)와 `assets_v1_2.sqlite`(기준선)에 의존. 이 두 파일을 지우면 v1.6·v1.7 모두 멈춤
- 폴더 구성이 바뀌면(앱 추가·삭제) 스캐너의 PROJECTS와 서비스의 MAIN_PROJECTS를 고쳐 v1.8로 만들 것. 폴더가 하나라도 없으면 새로 고침이 중단됨
- 검색 범위: 개발 프로젝트 6개 + 기술자산 00_GUIDE·60_AUDIT 문서. 30_REGISTRY·40_WORKING은 검색하지 않으므로 `/api/registry`에서 not_indexed로 나오는 것이 정상

## 시험 기록 (2026-11-12, Claude 원격 셸의 모의 환경)
- 실제 StudioProjects·TechAssets(읽기 전용 연결) + 합성 기준선 2,272행 + 등록부 v0.31
- 새로 고침 complete 3,841행 / registry: matched 29, superseded 4, stale 0
- '행정동' 검색: SERVER-ADDR-SEARCH-ADMIN-DONG-WITHDRAWN, CUSTOMER-DONG-NORMALIZE-TOOL-V2, CUSTOMER-REG-APP-01-* 표시
- Host 헤더가 다르면 403
- Mac 실제 실행 (2026-11-12 02:08, 사용자가 v1.7 앱 실행 → Claude 내장 브라우저로 확인): 서비스 v1.7 응답, 새로 고침 complete 3,915행, registry v0.31 — matched 68 / superseded 4 / stale 0 / not_indexed 64, '행정동' 검색에 재등록 자산 ID 표시
- **아직 확인 전:** LaunchAgent로 켜졌는지(아니면 실행기의 직접 실행으로 켜졌는지), 재로그인 후 자동 시작
