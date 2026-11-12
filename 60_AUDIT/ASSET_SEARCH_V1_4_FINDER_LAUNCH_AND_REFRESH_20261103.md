# 120. 라우터블 기술자산 검색 v1.4 — 단일 클릭·원자적 갱신 안전성 감사
검증 시각: 2026-11-03T19:38:16+09:00
원본 및 이전버전 불변: 기존 v0.5의 17개 자산 SHA-256 재확인 / v1.1~v1.3 코드·DB 미변경.

## 설치
Mac Finder 전용 앱: /Users/yongho/Applications/라우터블 기술자산 검색.app
Service: /Users/yongho/Library/Application Support/ROUTABL-AssetSearch/routabl_search_v1_4_service.py
메타데이터 검색 URL: http://127.0.0.1:8768/
Swift 네이티브 런처: 컴파일/자가시험/Info.plist 린트/앱 ad-hoc 서명 검증 통과.

## 실행 및 보안 시험 (모두 합격)
- 실제 macOS LaunchServices `open -g -a <app> --args --integration-test` 1회.
- 앱 경유 Python 서버 실행 확인; loopback 포트 바인딩 서버 하나만 존재함.
- 중복 Python 서버 재기동 시 flock 거절 확인.
- 로컬 HTTP / 및 /api?q=cloud_access.py 내용 검색 정상.
- 무인 또는 크로스사이트 갱신 요청은 403 거절, 세션 토큰·Origin 동시 검사 202 허용.
- 버튼과 동일한 HTTP POST로 수동 갱신 완료. 5,519행 -> 5,519행, 새 DB/이전 세대 DB 각각 quick_check=ok.
- 별도 테스트로 상태 조회만 반복하는 조건에서 단축 idle timeout 15초 후 자동 종료 PASS.
- Finder 앱 LaunchServices 기동 테스트 후 서버 종료; Terminal GUI 및 launchd 작업 실행 없음.
- 실제 브라우저 탭 열림 여부는 Finder에서 사용자가 앱을 더블클릭하여 확인 필요.

## 안전 설계
- 사용자의 클릭 없이 자동 재색인 없음, macOS 로그인 항목 또는 LaunchAgent 신규 생성 없음.
- 검색 서버는 기본 45분 동안 실제 검색/페이지 접근/갱신이 없으면 자동 종료. 단순 상태 polling은 제외.
- 인증 토큰은 매 서버 기동 시 새로 만들어짐. 외부 네트워크 송신 없음.
- 작업 도중 실패하면 이전 검색 DB는 보존, 이전 세대 복구 DB로 관리.
- 운영 앱/Firestore/GitHub/NAS 데이터에 변경 없음. 예약 백업 3개 비활성화 상태 유지.
- 인증정보 검출과 정규식 치환은 완전한 보안 보증 아님.
- 기존 NAS의 원본 검증 및 백업 자동화와 별도 문제.
- 신규 파일은 암호화 백업 완료 상태 아님.

## 사용법
/Users/yongho/ROUTABL-TechAssets/00_GUIDE/ASSET_SEARCH_V1_4_QUICKSTART_20261103.md
