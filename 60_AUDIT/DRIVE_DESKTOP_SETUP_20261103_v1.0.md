# 120. Mac Studio Google Drive Desktop 설치·연결 감사 v1.0
기준일: 2026-11-03 KST
변경대상: macOS Google Drive 데스크톱 앱 신규 설치(사용자 승인), 기존 라우터블 운영 소스·NAS·Firebase 미수정.

## 직접 확인
- 장치: Mac Studio Apple Silicon arm64, macOS 27.2.
- 다운로드 경로: ~/Downloads/GoogleDrive_Official_20261103.dmg
- 공급 서버: https://dl.google.com/drive-file-stream/GoogleDrive.dmg
- 다운로드 파일 크기: 139,866,706 bytes
- 다운로드 SHA-256: edfe08e00728c5084366f68a9e086a8ccafa3087bb0b47c2998148ac5db16661
- 설치 패키지: /Volumes/Install Google Drive/GoogleDrive.pkg
- pkgutil 서명 검사: Developer ID Installer Google LLC (EQHXZ8M8AV)
- Apple 공증: trusted by Apple notary service, spctl accept.
- 설치결과: /Applications/Google Drive.app 실물 존재, 앱 버전 133.0, 관련 프로세스 실행.
- Apple File Provider 로컬 위치: ~/Library/CloudStorage/GoogleDrive-[Google 계정 이름] 경로 발견.
- 기본 동기화 방향: 스트리밍 권장, 전체 내 드라이브 미러링은 설정하지 않음.

## 검증되지 않은 항목 / 장애
- File Provider 내 '내 드라이브' 폴더 열람은 원격 터미널에서 OSError errno 11 (Resource deadlock avoided).
- macOS Finder '위치' 내 Google Drive 사용 설정/권한 승인 상태는 도구상 직접 확인하지 못함.
- Google Drive 전용 폴더 ID 1AiXnryDvTGgcxX6cAi7IIJOs_nVn5fdS의 실제 업로드 파일은 조회 당시 0개.
- File Provider 경로를 통한 신규 파일 복사·자동 동기화는 미검증. 성공으로 보고하지 않음.
- 오류를 해결하기 위해 FileProvider DB 초기화, 캐시 삭제, 강제 종료, 운영 폴더 이동은 수행하지 않음.

## 준비한 수동 첫 업로드
- Finder 선택 파일: /Volumes/SSD2TB/ROUTABL-TechAssets-Backup/DriveStaging/ROUTABL-SecureBackup_NAS_AUTO_20261103_071957_KST.zip
- 약 69.7MB, 이전 NAS 소스와 ZIP 내부 17개 구성 파일의 SHA-256 대조 완료.
- Mac Safari 대상: https://drive.google.com/drive/folders/1AiXnryDvTGgcxX6cAi7IIJOs_nVn5fdS
- Safari 폴더에 위 ZIP 단일 파일을 복사 업로드한 후 실제 원격 파일 존재·크기·해시 대조 필요.
- AES-256 암호화된 sparsebundle의 블록만 ZIP에 저장. ZIP 자체 파일명·내부 경로 메타데이터는 암호화 대상이 아님.

## 향후 순서
1. 사용자가 File Provider 사용 설정 및 Google 계정 브라우저 로그인 필요한 단계 완료.
2. 업로드 사본이 Drive에 실제 저장됐는지 Google Drive 연결을 통해 확인.
3. 같은 계정의 Finder 스트리밍 폴더 접근과 원격 업로드/다운로드 검증.
4. 위가 성공한 경우에만 기존 04:30 로컬·05:00 NAS 백업 이후 Google Drive 자동 업로드 설정 검토.
