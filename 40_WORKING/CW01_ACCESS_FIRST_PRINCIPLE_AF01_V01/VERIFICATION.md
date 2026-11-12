# Digitopia AF-01 / 기술자산 후보 등록 준비 검증

- 작업일: 2026-11-08 KST
- 장치: MacStudioui-MacStudio.local
- 범위: 신규 격리 폴더에서 원칙 문서와 자산 등록 메타데이터 후보만 생성
- 작업 위치: /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_ACCESS_FIRST_PRINCIPLE_AF01_V01/
- 결과: 초안 저장 및 SHA 연결 PASS; 공식 등록 NOT_PERFORMED; 운영 적용 NOT_TESTED

## 파일별 SHA-256 (실제 파일 바이트 계산)
- DIGITOPIA_ACCESS_FIRST_PRINCIPLE_AF01_v1.0_20261108.md: 13eadac676aed2e97c0486edbed67c9db85a1d693545de80db209830614805d5
- REGISTRY_CANDIDATE.json: 8fde164399595e778da37019a259ea05247ab286df5ac7c25204c63ae2c71543

## 독립 확인
- 후보 JSON의 정책 문서 해시와 실제 파일 바이트 해시 연결: PASS
- 공식 대장 30_REGISTRY/asset_manifest_v0.27.json SHA-256: afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244
- 상기 공식 대장의 기대 SHA와 현재 실제 SHA 일치: PASS
- 신규 자산 ID ASSET-120-AF01-ACCESS-FIRST-V1.0의 공식 대장 포함 여부: FALSE
- 기존 00_GUIDE 원칙 문서와 B4~B6 백업 소스의 수정: 이번 작업에서 수행하지 않음
- Mac/NAS/검색/백업/권한/예약/게시 설정 변경: 수행하지 않음

## 후속
- 정식 등록·공식 게시 상태: BLOCKED / 별도 승인 및 현재 Step 5-C 게이트 유지
- 후속 AF-01 검색·증분 색인·다기기 접근 구현: 제안 단계, NOT_TESTED
- 기존 TI-01 중요도/복구 등급 및 보안 P0~P3는 보존하면서 별도 접근성 정책 축으로 연결함
- 검증서는 작업 파일 2건의 해시를 고정하는 기록이다. 검증서 자체의 해시는 후속 별도 읽기 확인으로 산출.
