# 120번 저장장치 암호화 추가 실사
검사일: 2026-11-03 KST
읽기 전용 명령: fdesetup status, diskutil info /System/Volumes/Data, diskutil info /Volumes/SSD2TB

## 실제 확인
- Mac Studio 내부 Data APFS 볼륨: FileVault is On / FileVault: Yes.
- 외장 SSD2TB APFS 볼륨: Encrypted: No / FileVault: No.
- NAS 암호화, Google Drive 백업 암호화/종단간 복원은 이번 회차에서 검사하지 않음.

## 운영 판정
Mac 내부 ~/ROUTABL-TechAssets/20_ORIGINALS의 로컬 사본은 FileVault 적용 볼륨에 있다.
외장 SSD2TB는 원본 기술자산 전체·고객자료·인증 파일을 직접 백업하는 대상에서 현재 제외한다.
관리 메타데이터 스냅샷만 외장 SSD에 작성했고, 파일 내용과 키가 없는지 앞으로도 검사해야 한다.
FileVault가 켜져 있어도 계정 탈취/실행 중 악성코드/백업 권한 오용까지 막아 주는 것은 아니다.

## 후속 승인
암호화 APFS 이미지 생성, Keychain 비밀번호 저장 정책, NAS·Drive 다중 위치 복구 구성은 실행 승인 후 진행.
기존 외장 SSD 파티션 변경·재포맷은 하지 않는다.
