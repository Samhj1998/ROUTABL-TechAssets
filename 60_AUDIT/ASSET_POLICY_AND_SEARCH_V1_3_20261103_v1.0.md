# 120번 기술자산 보안 분류 및 검색 확장 v1.3 — 실제 실행 감사
생성: 2026-11-03T19:09:04+09:00
기준: asset_manifest_v0.4.json, AssetSearch v1.2.
정책: 00_GUIDE/ASSET_SECURITY_AND_SEARCH_POLICY_v0.1.md

## 완료 및 검증
- Mac Studio 8개 개발 프로젝트 일반 기술자산 색인, 기존 NAS/로컬 색인 원본 미변경.
- v1.2 기존 2,272행 보존, v1.3 추가 3,247행, 최종 5,519행.
- 신규 일반 기술 텍스트 검색 1,998행, 메타데이터 전용 1,249행.
- 민감 파일명/경로 95개 색인 제외. 별도 외부 전송, 원본 코드 실행 없음.
- 신규 검색 DB SQLite PRAGMA quick_check=ok.
- HTTP 127.0.0.1:8767 웹 UI / 및 /api?q=cloud_access.py, TransportStatusPolicy, Firebase 실증 통과. 검사 후 서버 종료.
- 파일명/경로에 휴대전화·이메일 패턴 남은 신규 행 0.
- 검색 원문 저장은 로컬 전용이며, 비밀문자열 탐지의 완전성을 보장하지 않음.
- 기존 v0.4 등록 13개 파일 SHA256 재검증, 신규 4개 관리 파일의 해시 등록.
- 기존 2개 증거 파일의 GitHub/NAS 계보는 v0.4 결과를 승계하며 실행 검증 주장은 하지 않음.

## 보안등급·운영 허용
- P0: 비밀번호, API 비밀키, 패스키, 개인 SSH 키, Admin SDK 파일. 검색에서 제외.
- P1: 개인정보와 실제 거래자료. 원문 무차별 색인 금지.
- P2: 설정 및 아카이브, 미검토 자료. 경로/해시 등 메타데이터.
- P3: 일반 코드 및 기술문서. 민감 패턴 검사·치환 후 내용 검색 허용.
- 보통의 읽기·분석·검색에 추가 승인 요구 없음.
- 데이터 삭제, 운영 Firestore 변경, GitHub 배포, 백업본 교체는 별도 검증/승인 유지.

## 주의·후속
- 현재 새 DB는 기존 예약 암호화 백업의 포함 범위 밖. DB 재생성 가능하지만 원본 보존 수단은 아니다.
- 검색 v1.3은 1회 독립 구축판이고 자동 색인 갱신과 상시 웹서버 실행은 아직 하지 않았다.
- 이전 NAS 검색 DB의 전체 원문 보안 재감사는 이번 범위 밖이다.
- 예약 백업 3개 LaunchAgent는 사용자 안전 조치 이후 여전히 비활성화돼야 한다.
- 앱 소스, Firebase, NAS 원본, GitHub 원격 저장소에 쓰기/배포 수행하지 않았다.

## 결과물
- v1.3 엔진: /Users/yongho/Library/Application Support/ROUTABL-AssetSearch/routabl_assetsearch_v1_3.py
- v1.3 DB: /Users/yongho/Library/Application Support/ROUTABL-AssetSearch/assets_v1_3.sqlite
- v1.3 UI: /Users/yongho/Library/Application Support/ROUTABL-AssetSearch/routabl_web_v1_3.py
- 정책: /Users/yongho/ROUTABL-TechAssets/00_GUIDE/ASSET_SECURITY_AND_SEARCH_POLICY_v0.1.md
- v0.5 대장: /Users/yongho/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.5.json
