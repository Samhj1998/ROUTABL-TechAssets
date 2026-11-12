# 라우터블 기술자산 검색 v1.4 — 클릭 사용 안내
작성: 2026-11-03 | 120번 기술자산 통합관리

## 시작 (터미널 필요 없음)
1. Mac Studio Finder를 연다.
2. 메뉴 **이동 → 폴더로 이동**(Shift+Command+G)을 누른다.
3. `~/Applications` 입력 후 이동한다.
4. **라우터블 기술자산 검색.app**을 더블클릭한다.
5. 기본 브라우저에서 `http://127.0.0.1:8768/` 검색창이 열린다.

## 검색과 갱신
- 검색은 고객등록, cloud_access.py, TransportStatusPolicy, Firebase 등 키워드를 입력하고 검색한다.
- 소스코드 실행/수정 없이 기존 로컬 색인으로 조회한다.
- 최근 개발 내역이 검색되지 않으면 상단 **색인 새로 고침** 버튼을 클릭한다.
- 갱신은 사용자가 누른 경우에만 시작한다. 브라우저 화면에서 진행·완료·실패 상태를 확인한다.
- 갱신 성공 시 기존 검색 DB를 `assets_v1_4.previous.sqlite`에 복원용으로 보관한 뒤 새 DB를 원자적으로 교체한다.
- 갱신에 실패하면 이전 정상 색인이 유지되며 원본을 수정하지 않는다.
- 두 개의 원본 계보 검증파일이 기존 SHA-256과 달라지면, 이전 검증 주장을 유지하지 않기 위해 갱신을 중단할 수 있다.

## 자동 종료·중복 실행
- 동일 서버가 이미 동작 중이면 추가 서버를 만들지 않고 기존 서버에 연결한다.
- 최근 실제 검색/페이지 방문/갱신이 없는 상태가 45분가량 지속되면 로컬 검색 서비스가 자동 종료된다.
- 브라우저가 열린 채로 서버가 종료됐다면 앱을 다시 더블클릭한다. 자동 시작·상주·예약 기능은 없다.
- 종료된 서버는 사용자가 앱을 열기 전 다시 시작되지 않는다.

## 보안·데이터 유지
- 로컬 `127.0.0.1`만 수신한다. 외부 웹으로 기술자산을 업로드하지 않는다.
- 인증키/민감한 설정/개인정보 검색 정책은 기존 v1.3을 그대로 따른다.
- 화면의 갱신 요청은 동일 출처·세션 토큰 확인으로 제한된다.
- 검색용 색인 DB는 원본 자료 백업이 아니다. 코드 원본은 StudioProjects, 보존본은 NAS/GitHub 등에서 별도로 관리한다.
- 이전 v1.1~v1.3 검색 엔진과 DB, asset_manifest_v0.5.json은 그대로 둔다.
- 중지한 자동 백업 3개 예약은 활성화하지 않는다.

## 파일 위치
- 앱: `~/Applications/라우터블 기술자산 검색.app`
- v1.4 검색 서비스: `~/Library/Application Support/ROUTABL-AssetSearch/routabl_search_v1_4_service.py`
- v1.4 검색 DB: `~/Library/Application Support/ROUTABL-AssetSearch/assets_v1_4.sqlite`
- 이전 정상 검색 DB: `~/Library/Application Support/ROUTABL-AssetSearch/assets_v1_4.previous.sqlite`
- 개발 앱 소스/감사: `~/ROUTABL-TechAssets/40_WORKING/ASSET-SEARCH-V1_4/`, `~/ROUTABL-TechAssets/60_AUDIT/`

## 검증 한계
- 앱의 macOS LaunchServices 기동, 검색 서버 1개 생성, HTTP 검색, 중복 방지, 화면 갱신 인증, 원자적 교체 및 자동 종료를 시험했다.
- 실제 Finder 더블클릭으로 기본 브라우저를 여는 최종 사용자 UI 동작은 아직 사용자 실기기 확인이 남아 있다.
- 저장된 파일은 자동 백업 작업이 중지된 상태이므로 신규 백업의 완료를 주장하지 않는다.
