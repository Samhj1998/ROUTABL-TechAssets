# ChatGPT 공식 데이터 내보내기 1.59GB — AES-256 독립 SSD·NAS 백업·복원 최종 검증

**수행:** 2026-11-05, Mac Studio 사용자 yongho UID501.
**소스:** ChatGPT 공식 전체 데이터 ZIP (원본 보존).
**검증 영수증:** AES256_FULL_EXPORT_BACKUP_AND_RESTORE_20261105_v0.1.json.

## 1. 구분된 보관본
- 원본 FileVault 내부 ZIP: 1,589,174,843 bytes. SHA-256 `06efc5c5c787d59b7d1bd62566974563416b29792bb17ac318335475884c5553`.
- AES-256 APFS sparseimage 단일 암호화 컨테이너: 1,602,354,688 bytes. SHA-256 `6bae9eb926c80e28782d23597cd986a017c8de2290d304ff039e6213a6be5040`.
- 로컬 암호화 사본: `~/ROUTABL-TechAssets/20_ORIGINALS/ChatGPT-Account-Exports/2026-11-05/30_ENCRYPTED_LOCAL/ChatGPT-Account-Export-20261105_AES256.sparseimage`.
- 외장 SSD 암호화 사본: `/Volumes/SSD2TB/ROUTABL-PrivateEncrypted-Archives/ChatGPT-Export-20261105/ChatGPT-Account-Export-20261105_AES256.sparseimage`.
- NAS 암호화 사본: `/Volumes/Dev_Assets/ROUTABL-PrivateEncrypted-Archives/ChatGPT-Export-20261105/ChatGPT-Account-Export-20261105_AES256.sparseimage`.
- NAS 독립 복구 시험 사본: Mac FileVault 내부 `30_ENCRYPTED_LOCAL/NAS_INDEPENDENT_RECOVERY_ChatGPT-Account-Export-20261105_AES256.sparseimage`. 검증 근거로 보존.

## 2. 수행 및 무결성 판정
1. macOS 로그인 Keychain에 무작위 고강도 암호를 생성·저장하고 같은 세션에서 재조회 확인. 암호 내용은 코드·명령행 인수·파일·영수증에 남기지 않음.
2. `hdiutil create -encryption AES-256` 명시. 생성 디스크 이미지 `imageinfo`의 `Properties.Encrypted=True` 대조.
3. 암호화 볼륨에 공식 ZIP 원본 파일명 그대로 복제, 내부 원본 ZIP SHA-256 일치 및 ZIP CRC 검사 PASS.
4. 볼륨 마운트 해제 후 암호화 파일을 SSD·NAS에 별도 복사. 각 사본 SHA-256과 파일 크기 100% 일치.
5. **SSD 사본**을 독립적으로 읽기 전용 마운트하고 ZIP을 읽어 원본 SHA-256 및 CRC PASS 확인, 재잠금.
6. **NAS 사본**을 SMB에서 FileVault 내부로 다시 복사하여 암호문 SHA-256 재검사, 이 복구 사본을 읽기 전용 마운트해 ZIP SHA-256 및 CRC PASS 확인, 재잠금.
7. 최종 모든 임시 암호화 볼륨 마운트 해제 확인. 원본 `Downloads` ZIP과 기술자산 원본, 기존 NAS CAS 백업 및 정기 실행 작업은 변경하지 않음.
8. Google Drive 업로드·NAS pruning·백업 원본 삭제 없음.

## 3. 중요 잔여 위험 — 암호 보관처 독립성
**KEY_ESCROW_PENDING**: 키는 현재 `/Users/yongho/Library/Keychains/login.keychain-db`에 연결된 로컬 로그인 키체인에만 저장됨. 원래 맥 전체를 잃거나 로그인 키체인을 복구할 수 없으면, SSD·NAS의 암호화 파일도 복구할 수 없을 수 있음. **암호문 복원 시험은 통과했지만 독립 기기의 비밀번호 복구 검증은 아직 완료하지 않았다.**
- 복구 접근 서비스 식별자: `com.routabl.techassets.chatgpt-export-20261105.aes256`. 실제 암호값은 기록하지 않음.
- 사용자가 별도 신뢰할 수 있는 비밀번호 관리 앱 또는 물리적 오프라인 복구 수단에 안전하게 기록하도록 안내 필요.
- 비밀번호를 채팅·이메일·GitHub·기술자산 파일·평문 NAS에 넣지 말 것.
- 복구 수단 확보 후 새 맥/분리 시험 환경에서 실제 잠금 해제와 ZIP SHA 검증하여 재해복구 완료로 승격할 것.

## 4. 작업 경계
- 본 작업은 **2026-11-05 공식 내보내기 단일 시점 스냅샷**에 대한 독립 백업이다. 이후 새 ChatGPT 데이터가 자동으로 반영되는 정기 작업이 아님.
- 기존 ROUTABL v2.1 자동 백업(파일당 105MB 제한) 및 NAS CAS 백업과 별도로 수행. 그 설정·코드·스케줄은 변경하지 않음.
- SSD2TB 자체는 암호화하지 않았으나, 저장된 공식 내보내기 사본은 **AES-256 이미지 내부**에만 있음. NAS에도 평문 ZIP을 직접 전송하지 않음.
- MAC과 NAS는 물리적으로 동일 장소일 수 있으므로 별도 화재·도난 대비 외부 보관은 별개 과제.
- 자산 등록부에는 원본 ZIP과 암호화 이미지 자체를 넣지 않고, 비공개 메타데이터와 파일 경로·SHA만 기록한다.

**최종 판정:** SSD/NAS 독립 암호화 백업 + 소스 무결성 및 실제 복원 PASS. Key Escrow 및 완전 재해복구는 OPEN.
