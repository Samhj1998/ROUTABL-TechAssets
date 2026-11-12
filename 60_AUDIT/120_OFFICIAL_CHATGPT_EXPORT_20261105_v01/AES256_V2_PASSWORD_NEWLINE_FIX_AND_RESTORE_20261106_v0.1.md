# 라우터블 ChatGPT 공식 내보내기 AES-256 백업 v2 — 암호 줄바꿈 결함 수정 및 복원 검증

**수행:** 2026-11-06 KST, Mac Studio UID 501  
**변경 목적:** 2026-11-05 v1 이미지의 Finder 직접 잠금 해제 시 인증 오류를 해결하기 위해, 기존 로그인 키체인과 Apple 암호 앱에서 확인된 원래 암호값으로 **새로운** v2 이미지를 작성. 기존 v1·ZIP·개발 앱 코드를 건드리지 않음.

## 1. 결함 분석과 수정 경계

- v1 프로그램은 `hdiutil -stdinpass`에 암호 뒤 줄바꿈 바이트를 추가하여 호출함. Apple/macOS `hdiutil` 설명서는 `-stdinpass`에서 종료 NUL 앞의 줄바꿈 문자가 암호에 포함될 수 있다고 경고함.
- 사용자가 Finder에서 원래 암호를 입력하면 인증 오류가 발생했지만, v1 프로그램은 같은 줄바꿈을 포함한 입력으로 복원에 성공하는 현상이 나타남.
- v1 암호에 줄바꿈이 포함된 점은 **소스 코드 및 문서와 현상에 강하게 부합**하나, 도구의 보안 제한으로 v1 이미지에 원래 암호만 전달하여 대조하는 직접 부정시험은 실시하지 못함. 추론과 직접 검증을 혼동하지 않음.
- v2는 기존 로그인 키체인 서비스 식별자 `com.routabl.techassets.chatgpt-export-20261105.aes256`을 그대로 사용하고 암호 문자열을 변경하거나 재발급하지 않음.
- v2의 `hdiutil -stdinpass` 호출은 `password+bytes([0])`으로, **줄바꿈 없이 NUL 종결**을 사용함. NUL은 입력 종료 표시이며 실제 암호 문자열에 추가하지 않음.
- 원본 v1 실행 프로그램 `private_export_aes256_offsite_v01.py` 및 v1 이미지 파일은 수정·삭제하지 않음.

## 2. 새 v2 암호화 사본

- 입력 ZIP 크기: 1,589,174,843 bytes.
- 원본 ZIP SHA-256: `06efc5c5c787d59b7d1bd62566974563416b29792bb17ac318335475884c5553`.
- v2 이미지 형식: AES-256 encrypted APFS sparseimage, 1,602,354,688 bytes.
- v2 이미지 SHA-256: `a8ddc65acc2382aab9ec0cc792ffc5b20c847a337ce58dd8eca2d856698bd5f4`.
- 새 로컬 이미지: `~/ROUTABL-TechAssets/20_ORIGINALS/ChatGPT-Account-Exports/2026-11-05/40_ENCRYPTED_V2_LOCAL/ChatGPT-Account-Export-20261105_AES256_v2.sparseimage`.
- 새 외장 SSD 이미지: `/Volumes/SSD2TB/ROUTABL-PrivateEncrypted-Archives/ChatGPT-Export-20261105-v2/ChatGPT-Account-Export-20261105_AES256_v2.sparseimage`.
- 새 NAS 이미지: `/Volumes/Dev_Assets/ROUTABL-PrivateEncrypted-Archives/ChatGPT-Export-20261105-v2/ChatGPT-Account-Export-20261105_AES256_v2.sparseimage`.

## 3. 수행된 독립 검사

1. v2 새 이미지 생성 성공, `hdiutil imageinfo`로 암호화 활성화 확인.
2. 같은 기존 키체인 암호를 줄바꿈 없이 전달해 v2 이미지를 마운트하고 공식 ZIP을 쓴 뒤 SHA-256·CRC 검사 PASS.
3. 외장 SSD와 NAS 암호화 사본의 SHA-256가 각각 v2 로컬 이미지와 일치.
4. SSD 암호화 이미지에 **읽기 전용**으로 잠금 해제하여 원본 ZIP SHA·CRC 확인 PASS.
5. NAS 암호화 이미지를 FileVault 내부로 독립 복사해 SHA를 대조하고 읽기 전용으로 잠금 해제, ZIP SHA·CRC 확인 PASS.
6. 최종 마운트 해제 확인. 구 v1 이미지 파일과 원본 ZIP 및 다운로드 ZIP은 그대로 유지.
7. Google Drive 업로드, NAS pruning, 기존 오전 4:30 LaunchAgent 설정 변경은 실시하지 않음.

**최종 검증 영수증:** `AES256_FULL_EXPORT_BACKUP_AND_RESTORE_20261106_v0.2.json`  
**영수증 SHA-256:** `d154a8d7568ad2092e86ea9b8c6650b797335d96c0c0cbdb0f2c168e4edeff9b`.

## 4. 남아 있는 사용자 GUI 검증

- Finder의 디스크 이미지 더블클릭, Apple 암호 앱에서 복사한 비밀번호 붙여넣기, 실제 ZIP 표시: **사용자 실기기 검증 전.**
- 프로그램이 줄바꿈 없이 열리는 것은 확인되었으나 Finder의 실제 수동 입력 흐름 성공으로 확대하지 않음.
- v2 이미지에서만 첫 시험하며, 이번에는 **'내 키체인에 암호 기억'을 체크하지 않고** 시도해 기존 키체인 항목 간 혼동을 피함.
- 시험 성공 후 암호화 볼륨을 Finder에서 추출하여 닫음. 기존 v1 이미지는 암호 입력 오류 원인 보존을 위해 유지.

## 5. 재해복구 경계

- Apple 암호 앱에서 동일한 암호 항목이 iPhone에 동기화된 것은 사용자가 별도로 확인했음.
- 맥스튜디오가 없어도 다른 Mac에서 v2 이미지가 열리는지 실제 복원한 기록은 아직 없음.
- Mac Studio/SSD/NAS가 한 장소라면 독립 물리적 재해복구는 별도 과제.
- 이 작업은 2026-11-05 **단일 공식 내보내기 스냅샷**, 이후 ChatGPT 전체 데이터 자동 동기화가 아님.

**판정:** 암호 줄바꿈 처리 수정 및 새 v2 암호화 SSD/NAS 백업·실제 읽기전용 복원 PASS. Finder 수동 GUI와 타기기 재해복구 별도 OPEN.
