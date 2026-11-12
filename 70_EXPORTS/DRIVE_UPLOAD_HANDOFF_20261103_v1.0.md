# ROUTABL 암호화 백업 — Google Drive 업로드 인계
기준: 2026-11-03. 상태: 업로드 대기(미완료).

## 준비된 파일 (Mac Studio 외장 SSD)
Finder에서 Command+Shift+G 입력:
/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/DriveStaging

최신 업로드 ZIP:
ROUTABL-SecureBackup_NAS_AUTO_20261103_071957_KST.zip
크기: 69,725,994 bytes
SHA-256: 45bd23b30cbc84fb0e156e8a1e878a22e84dae13e8659c8616167e355c6d5389

## 대상 Google Drive 폴더
https://drive.google.com/drive/folders/1AiXnryDvTGgcxX6cAi7IIJOs_nVn5fdS
Folder ID: 1AiXnryDvTGgcxX6cAi7IIJOs_nVn5fdS
기존 운송 데이터 Backup_SmartDispatch_Data 폴더에 올리지 않는다.

## 한 번 업로드하는 방법
1. Mac Studio에서 위 Drive 폴더 URL을 브라우저로 열고 해당 계정으로 로그인한다.
2. Finder의 위 ZIP을 Drive 폴더로 끌어 놓는다. 폴더 전체나 .sparsebundle을 업로드하지 않는다.
3. 업로드 완료를 확인한다. ChatGPT에는 백업 비밀번호나 키를 입력하지 않는다.
4. 새 채팅에서 '120번 Google Drive 업로드 확인 및 SHA 복원 검증'을 요청하면 Drive에 저장된 파일을 읽기/다운로드하여 일치 검증한다.

## 자동화 남은 요구
이후 매일 자동 업로드까지 하려면 Mac Studio에 Drive로 파일을 전송할 별도 경로가 필요하다.
Google Drive for desktop 설치·로그인 또는 승인된 Drive API 토큰/연동으로 구현하되, 비밀키를 코드에 넣지 않는다.
동기화할 때는 이미지가 잠긴 상태에서 이미 완성된 ZIP만 전송한다.
현재 Drive 폴더는 생성됐으나 내부 파일은 0개로 확인되었다.
