# ROUTABL-TechAssets 운영 안내 v0.1
기준일: 2026-11-03 (KST) | 프로젝트: 120. 라우터블 기술자산 통합관리체계
상태: 기반 디렉터리 설치 및 선택 자산 메타데이터 실사 단계. 전체 자산 이관·백업 완료 아님.

## 기준 저장소와 역할
- 기준 관리 경로: /Users/yongho/ROUTABL-TechAssets
- 기존 검색 프로그램/DB 유지: ~/Library/Application Support/ROUTABL-AssetSearch
- 기존 NAS 원본 경로 유지: /Volumes/Dev_Assets/Routabl
- 기존 로컬 업무 백업 유지: ~/ROUTABL-Backups
- 00_GUIDE: 운영 규칙, 10_INBOX: 수집 대기, 20_ORIGINALS: 출처별 무수정 복제본
- 30_REGISTRY: ID/경로/해시/계보/검증, 40_WORKING: 편집 작업, 50_VERIFIED: 증거 있는 승인판
- 60_AUDIT: 실사·시험 기록, 70_EXPORTS: AI 및 외부 이관용 안내문

## 현재 상태
20_ORIGINALS 아래 5개 출처 폴더만 생성. 실제 원본 복사·승격 미실시.
30_REGISTRY/asset_manifest_v0.1.json은 7개 '선택 자산'의 위치와 현재 SHA-256을 담은 초기 파일이다.
전체 NAS/Library/Mac 원본을 포괄하는 자산대장으로 간주하지 말 것.

## 비파괴·보안 규칙
1. 역사적 원본, 백서 봉인본, 운영 프로젝트, Firebase, 기존 NAS 자료는 사용자 승인 없이 수정하지 않는다.
2. 새 파일 생성은 지정된 ROUTABL-TechAssets 안에서만 한다. 기존 파일은 덮어쓰지 않고 새 버전명을 붙인다.
3. 원본과 사본을 구별하고, 파일 해시 확인·업무 실행 성공·복원 성공을 별도 판정한다.
4. 암호, 인증키, 개인 식별정보, Firebase Admin SDK JSON, API 토큰을 관리 색인이나 공유 문서에 그대로 넣지 않는다.
5. 원본 검색 실패, 저장 장치 접근 실패, 검색 DB 범위 밖, 파일 부재를 각각 구분한다.
6. A=안전한 읽기/검증, B=지정 폴더 안 신규 비파괴 파일 생성, C=운영 데이터/원본 변경·배포·계정/권한 변경으로 구분한다.
7. 기존 증거에 '과거 성공'이 있더라도 현재 API 권한이나 운영 앱의 성공을 자동 보증하지 않는다.

## 다음 단계 관문
- 핵심 자산부터 출처별 목록과 해시를 늘리고, 해당 자산을 재발견할 수 있는지 테스트한다.
- 복제 작업은 복제 전후 SHA-256과 복원 시험 계획을 작성한 후 수행한다.
- 새 AI 채팅 인계는 70_EXPORTS/AI_ASSET_DISCOVERY_v0.1.md를 참고한다.
