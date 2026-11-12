# ASSET-SECURITY-01 암호화 백업 초기 설정 기록
기준일: 2026-11-03 KST
실행 장치: MacStudioui-MacStudio.local / 계정 yongho

## 준비 및 실행
- 전체 외장 SSD 암호화, 재포맷, 파티션 조정 없음.
- 대상: /Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle
- 목표: 20GB Sparse Bundle / APFS / AES-256 / 볼륨명 ROUTABL-Secure
- 로컬 1회 설정 스크립트: ~/ROUTABL-TechAssets/00_GUIDE/SETUP_ROUTABL_SecureBackup.command
- 스크립트는 비밀번호/인증키를 인자로 전달하거나 파일에 저장하지 않음.
- Terminal에서 Mac 사용자의 암호 직접 입력을 요구하는 hdiutil create -agentpass 실행.
- 명령 프로세스가 동작 중이며 .sparsebundle 경로가 나타난 것만 확인됨.
- 현재 상태: WAITING_FOR_LOCAL_PASSWORD / IMAGE_NOT_YET_VERIFIED.
- 파일 존재만으로 암호화 설정, 키체인 연동, 이미지 완성, 백업 성공을 판정하지 않음.

## 안전 제약
- 비밀번호는 ChatGPT 대화에 보내지 않는다.
- 이미지 생성 후 Finder에서 최초 마운트할 때 '키체인에 저장' 선택 여부를 사용자가 직접 확인한다.
- 암호/복구 수단은 Mac 키체인 외에 사용자 관리의 별도 안전한 위치에도 보관한다.
- 해시 대조 전까지 이 이미지에 원본 자료를 넣지 않음.
- 비밀번호 입력을 취소하거나 실패했다면 부분 생성물이 있을 수 있으므로 임의 삭제하지 말고 확인한다.

## 후속 실제 검증(미실시)
1. 이미지 생성 완료와 AES-256·APFS·20GB 메타데이터 확인.
2. Finder 마운트와 키체인 재사용 확인(암호 노출 없이).
3. 테스트 파일 복제, 분리, 재마운트, 해시 대조.
4. 승인된 기술자산 스냅샷 백업·복구와 자동 분리.
5. 변경 없는 원본 및 새 이미지 상태 최종 감사.
