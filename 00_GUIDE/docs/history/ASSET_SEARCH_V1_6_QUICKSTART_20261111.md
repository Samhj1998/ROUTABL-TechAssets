# 120. 라우터블 기술자산 통합검색 v1.6 — Mac에서 사용하기

작성: 2026-11-11 | 대상: Mac Studio | v1.5·v1.4 보존

## 열기
- `~/Applications/라우터블 기술자산 검색 v1.6.app` 더블클릭 → `http://127.0.0.1:8770/`
- v1.5(8769)는 그대로 남아 있지만, 옛 작업본 4개 폴더가 정리되어 **v1.5의 새로 고침은 실패**합니다. v1.6을 쓰세요.

## v1.5와 달라진 점
- 검색 대상: 기사앱(고객앱 customer-android 포함), 시니어앱, 일상점검표, Firebase 이관 도구, **분석앱** + 기술자산 **00_GUIDE·60_AUDIT 문서(.md/.txt)**
- 제외 유지: 20_ORIGINALS, ChatGPT 내보내기, 백업, 인증키·개인정보 경로 (전화·이메일은 [PHONE]/[EMAIL]로 가림)
- 등록부: 30_REGISTRY의 **최신 asset_manifest를 자동 선택** (설치 시 v0.29). 자산 ID 표시 2건 → 53건
- 범위 선택에 **기술자산 문서** 추가. 문서도 Finder 위치 보기 가능 (00_GUIDE·60_AUDIT 안만)
- 별명: 분석앱, 공통코드, 해시검사, 읽기전용, 인계, 분업, 고객앱
- 시작 기준 색인: NAS 기준선 v1_2(2,272행). 첫 새로 고침 후 3,832행 (2026-11-11 15:05)

## 새 파일이 안 보이면
- 화면의 **검색 목록 새로 고침**. 실패해도 기존 색인 유지, 직전 색인은 `assets_v1_6.previous.sqlite`로 보관

## 파일
- 서비스: `~/Library/Application Support/ROUTABL-AssetSearch/routabl_search_v1_6_service.py`
- 스캐너: 같은 폴더 `routabl_assetsearch_v1_6_scanner.py`
- 색인: `assets_v1_6.sqlite` / 직전: `assets_v1_6.previous.sqlite`
- 실행기: 셸 스크립트 `RoutablSearch16` (v1.5의 Swift 실행기는 v1.5 경로가 고정되어 재사용 불가)
- 작업 원본·시험 기록: `40_WORKING/SEARCH_V1_6_20261111/`

## 알아둘 점
- 등록된 자산(SHA 일치)이 가산점을 받아, '정산' 같은 넓은 검색어에서는 분석앱 문서가 기사앱 Settlement.kt보다 위에 나올 수 있음
- 폴더 구성이 바뀌면(앱 추가·삭제) 스캐너의 PROJECTS를 고쳐 v1.7로 만들 것. 폴더가 하나라도 없으면 새로 고침이 중단됨
