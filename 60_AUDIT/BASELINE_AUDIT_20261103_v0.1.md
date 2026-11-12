# 120. 선택 기술자산 1차 실사 보고 v0.1
확인일: 2026-11-03 KST
방식: Remote Desktop Commander를 통한 Mac Studio 읽기 전용 검사 및 새 관리 폴더 내 보고서 생성.
기존 코드/DB/NAS/Firestore/GitHub에 변경 없음.

## 기존 ASSET-SEARCH-01 v1.1 DB
위치: ~/Library/Application Support/ROUTABL-AssetSearch/assets.sqlite
SQLite PRAGMA integrity_check: ok (읽기 전용 연결)
총 2,270 (일반 파일 1,024 / ZIP 내부 파일명 1,246)
본문 검색 가능 status=OK 223, METADATA_ONLY 778, PDF_TEXT_NOT_EXTRACTED 23,
ZIP_MEMBER_METADATA_ONLY 1,246.
수동 등록 기술자산: TA-CASE-20261102-01, INTEGRATION-F1, INTEGRATION-E04.
현재 NAS 루트 /Volumes/Dev_Assets/Routabl 경로는 접근 가능.
원본 NAS 봉인본과 최근 수정 이력 전체 검증은 이번 범위에서 제외.

## 성공사례 cloud_access.py 실증
실제 존재: /Users/yongho/StudioProjects/ROUTIVEL-Firebase-Migration/tools/firebase-migration/cloud_access.py
파일 크기 3,995B, SHA-256 de08b060d03a6b6c9f155cf89673f2285a67502cf664442b1a9bc835529a54e5
Python AST 파싱 성공, 최상위 클래스: APIError, CloudAPI.
기존 docs 내 cloud_access.py 파일 경로: 0건.
v1.1 query 'cloud_access.py': 일반 검색 0건, 과거 사례 수동 등록 1건.
따라서 '실제 파일 존재'와 '현재 NAS 범위 색인'이 불일치한다.
2026-11-02 주소록 사례 보고서는 과거 Work 성공 로그의 증거다.
이번 회차에서는 Firebase 읽기/쓰기, 인증 확인, 실제 고객 등록을 실행하지 않았다.

## 조회 스모크 테스트 (1회 표본)
cloud_access.py : 약 257.0ms, 일반 검색 0건 / 수동 1건
주소등록 : 약 222.7ms, 일반 검색 111건 / 수동 1건
초성검색 : 약 267.7ms, 일반 검색 591건 / 수동 0건
이 수치는 1회 실행시간으로 성능 SLO나 95백분위 결과를 의미하지 않는다.

## 1차 확인한 별도 자산
INTEGRATION-F1 소스 파일 존재·SHA 계산됨. 과거 정적 검토와 현 APK 검증은 별개.
검색 엔진 소스, 로컬 웹 UI, 기존 DB, 소스 ZIP, NAS README의 경로·해시 확인됨.
선택 자산 7개 결과는 30_REGISTRY/asset_manifest_v0.1.json 참고.
INTEGRATION-E04의 현재 물리 원본/Library 위치 동일성 검증은 미실시.

## 위험 및 다음 개선 순서
P0-1: NAS 중심 검색 인덱스가 Mac Studio 로컬 프로젝트를 포괄하지 못함.
P0-2: 원본 보존/복제본 검증/운영 성공 세 상태가 분리되지 않음.
P1-1: PDF·코드 본문 색인 및 ZIP 멤버 해시 없음.
P1-2: ChatGPT Library 전체 수집 범위·공식 자동 동기화 가능성 미검증.
P1-3: 민감정보 필터의 포괄성 검증 필요.
다음 작업: 인덱스 갱신 코드 변경 전에 원본 목록·출처 계약·백업·허용 경로를 확정.

## 현재 수행하지 않은 작업
운영 Firebase 변경, GitHub push/commit, 원본 복제/삭제/이동, NAS 백업 덮어쓰기,
검색 DB 재색인(build), ChatGPT Library 자동 다운로드, NAS 오프라인 복원 시험.
