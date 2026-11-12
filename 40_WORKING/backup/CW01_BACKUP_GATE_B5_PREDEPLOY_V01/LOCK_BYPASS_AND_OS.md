# 공통 잠금 우회 및 OS 경계

| 진입 경로 | 관찰된 잠금 또는 영향 | 대응 |
| --- | --- | --- |
| native.v02 → 감독자 v0.1 | native_backup_supervisor_v01.lock | 운영 전환 승인 후 등록 해제 및 재등록 차단 |
| native.v042 → 감독자 v0.2 | native_backup_supervisor_v02.lock | v042 단독 확인 뒤 승인된 순서로 해제 |
| OneShot v0.1 run | manual_mac_to_nas_cas_v01.lock | 수동 진입을 동일 신규 감독자에 연결하고 구 런처의 쓰기 접근 제거 |
| HeadlessDailyGate v0.3 run local/nas | selective_v21_gate_local.lock 또는 selective_v21_gate_nas.lock | 전용 실행 경로 아래로 제한. check도 자체 잠금 경로를 열므로 승인 없는 운영 호출 금지 |
| SelectiveSecureBackup v2.1 backup | selective_v21.lock, SSD 이미지 접근 | 원본 코드가 직접 실행돼도 쓰기 못하도록 저장 매체 권한으로 제한하거나 별도 승인 하에 진입 검증 추가 |
| NAS CAS v0.2 seed/capture | CAS/writer.lock, NAS 메타데이터·blob 쓰기 | 기존 NAS 권한만으로 공통 잠금 소유권이 강제되지 않음. NAS 쓰기 자격을 전용 실행 서비스에 한정 |
| SelectiveNasCopy v2.1 및 NASReplication v1.0 | selective_nas_v21.lock 또는 nas_copy.lock | 별도 쓰기 경로를 제한. Gate nas 호출을 쓰지 않는 운영 프로파일을 승인 핀으로 명시 |
| 이전 Local/NAS 예약 스크립트·수동 .command | ScheduledBackup의 backup.lock 및 별도 NAS 잠금 | 플리스트 파일 존재와 작업 로드 구분. gui/501의 daily, nas.daily, drive.daily는 조회 시 미등록. 다른 도메인·직접 실행은 별도 점검 |

이 목록의 기술적 우회 차단 상태는 NOT_VERIFIED다. 사용자와 서비스가 같은 UID 및 같은 매체 쓰기 자격을 공유하면, 기존 바이트를 누구나 Python으로 실행 가능한 상황에서 감독자의 flock만으로 차단할 수 없다. 파일 실행 비트를 내리는 조치만으로도 Python 직접 호출을 차단할 수 없다. 전용 쓰기 자격의 매체 정책, 보호된 서비스 경로, 수동 요청을 받는 IPC를 함께 검증한다. 기존 엔진이 사용자 홈·Keychain·실행 UID를 전제하므로 전용 UID 도입이 실제 권한 조건과 양립하지 않으면 적어도 쓰기 진입부에 새 판본이 필요하다.

## 위험별 수용 기준

- 프로세스 그룹 이탈. macOS 가상 자식이 setsid()로 이탈하면 원래 그룹에 보낸 종료 신호를 피한다는 점을 시험했다. 파이프 종료로 시험 자식을 회수했다. 운영에서는 서비스가 생성한 프로세스의 추적·정리와 독립적인 잔존 확인이 필요하다. 확인 실패 시 재시도 및 매체 재사용을 보류한다.
- 잠금 inode 교체. 교체된 경로의 다른 inode에도 flock을 잡을 수 있음을 시험했다. 신뢰하는 서비스 전용 디렉터리에서 O_NOFOLLOW와 fstat/lstat의 dev·ino를 대조하고, 원본 inode 교체나 unlink를 막는다. 해시 또는 경로 대조만으로 이미 시작한 작업의 경합을 되돌릴 수 없다.
- 승인 핀 후 코드 교체. 같은 경로의 새 바이트와 열린 FD가 달라지는 사례를 시험했다. 운영에서는 실행 전에 신뢰되는 불변 릴리스와 모든 import를 검증하고 동일 바이트만 실행한다. 경로 재오픈 및 바이트코드·사용자 import 경로를 통제한다.
- 비정상 종료와 마운트 잔류. 프로세스가 사라져도 이미지가 분리됐다는 증거가 되지 않는다. 신규 작업 전·종료 후 소유 작업 ID, 마운트/이미지 장치 식별자와 프로세스 상태를 독립 확인한다. 다른 사용자의 마운트를 강제 해제하지 않는다. 실제 암호화 매체 장애·복구는 별도 승인된 운영 수용시험에서만 수행한다.
