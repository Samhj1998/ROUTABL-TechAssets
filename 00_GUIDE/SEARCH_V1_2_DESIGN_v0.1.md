# ASSET-SEARCH-01 v1.2 비파괴 확장 설계 (코드 수정 전 명세)
기준: 2026-11-03 KST / 상태: 설계안, 실제 구현 미착수
기존 검색엔진: ~/Library/Application Support/ROUTABL-AssetSearch/routabl_assetsearch_v1_1.py
기존 DB: assets.sqlite (현재 2,270항목, 읽기 전용 기준선 유지)

## 1차 목표
- 조회 요청 'cloud_access.py'가 로컬 소스 실물 1건과 과거 검증 사례 TA-CASE-20261102-01을 함께 찾도록 한다.
- NAS 마운트 없이 Mac의 검증 자산 색인을 읽을 수 있어야 한다.
- 기존 DB 및 NAS 원본, 운영 코드와 자료를 변경하지 않는다.

## 승인 후 시험 환경 제안
- 신규 독립 시험 DB: ~/ROUTABL-TechAssets/40_WORKING/assets_v1_2_test.sqlite
- 실행 코드는 기존 v1.1 소스와 별도 버전으로 작성. v1.1 원본 절대 덮어쓰기 금지.
- 대상 루트는 고정된 읽기 허용 목록만 사용:
  1) /Volumes/Dev_Assets/Routabl (기존 NAS 보관)
  2) ~/ROUTABL-TechAssets/20_ORIGINALS (Mac에서 검증된 사본)
  3) ~/StudioProjects/ROUTIVEL-Firebase-Migration/tools/firebase-migration (초기에는 파일명·해시 등 메타데이터만)
- 이 외의 StudioProjects 전체를 무차별 색인하지 않는다. 외부 저장장치와 심볼릭링크는 자동 탐색하지 않는다.

## 민감정보 통제
- 기본 허용은 경로, 파일 크기, 수정시각, SHA-256 및 승인 태그.
- .env, 인증서, 서비스계정 JSON, Admin SDK, private key, 토큰, .git, node_modules, 빌드 산출물 등 제외.
- .py/.kt 등 실행 소스는 1단계 본문 미수집: AST 식별자 같은 안전한 메타데이터만 추후 검토.
- 문서 본문은 인덱스 저장 전 개인정보·비밀정보 검사와 허용 확장자/크기 제한.
- 검색 결과에서 승인 없는 자동 코드 실행, 운영 Firebase write 요청 생성 금지.
- 원본 URL·Library ID·Git SHA는 출처 정보로만 관리, 검증상태와 별개로 저장.

## 검증 및 합격 기준
- cloud_access.py: 실물 경로와 과거 성공사례 모두 상위 결과에 표시.
- '주소등록', '초성검색', '취소상태', '97-1 v4.1' 등 대표 검색 20건의 상위 3개 정답 19건 이상.
- 95백분위 검색 지연 2초 이하(여러 회 측정, 일회성 응답시간과 구분).
- NAS 미마운트 상태에서도 Mac 내부 사본·레지스트리 조회 성공(마운트 해제 작업은 별도 승인/시험 창에서).
- DB 신규 파일은 기존 DB와 무결성·건수·검색 품질 차이를 비교, 기존 파일 덮어쓰기 금지.
- 민감정보 테스트 데이터는 합성값으로 구성, 실제 비밀키 사용 금지.

## 아직 승인되지 않은 변경
v1.2 코드 작성·실행, 신규 테스트 DB 색인 생성, 기존 검색서버 전환은 별도 실행 결정.
