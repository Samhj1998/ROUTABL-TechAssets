# B4 엔진 호환성 및 격리 경계

| 대상 | 소스에서 확인한 계약 | 운영 재사용 판정 |
| --- | --- | --- |
| HeadlessDailyGate v0.3 | ALREADY_RUNNING은 exit 0과 executed=false. SKIPPED_CURRENT_SNAPSHOT_VERIFIED는 기존 영수증 재사용 후보다. READY는 준비 출력이며 run의 별도 SUCCESS 및 receipt_chain_verified=true가 완료 증거다. | 동일 바이트 재사용 후보. 실제 실행 및 입력·출력 호환성 미검증. Gate는 check에서도 자체 잠금 파일을 열므로 운영 check를 실행하지 않았다. |
| SelectiveSecureBackup v2.1 | 최신 v0.N 선택, 정렬된 선택 목록 해시, 영수증 바이트 SHA, source_bytes, 잠금 및 SHA 상태를 제공한다. | 동일 바이트 재사용 후보. 실제 선택기, 제외·크기 규칙 및 스냅샷 재현 미검증. |
| NAS ContentAwareBackup v0.2 | SNAPSHOT_ALREADY_INDEXED는 재사용이며 검증 기본값은 전체 구성요소 해시를 보장하지 않는다. INCREMENTAL_SNAPSHOT_VERIFIED는 신규 색인 결과이며 full 검증을 수행한다. | 동일 바이트 재사용 후보. 운영 재사용에는 full verify, 실제 CAS 매니페스트 및 영수증 연결 확인이 필요하다. |

격리 코드는 후보 폴더의 가상 대장 바이트와 선택된 파일 바이트로 지문을 계산한다. 로컬 영수증 바이트의 SHA를 가상 상태 보고서와 대조하고, NAS CAS는 스냅샷 ID, 로컬 영수증 SHA, 대장 및 선택 목록 SHA를 연결한다. 단일 가상 암호문 구성요소 해시도 직접 대조한다. 실제 로컬 영수증은 summary/records와 상태 보고서에 필드가 분산된다. 이 후보의 정규화된 가상 형식을 운영 파일 형식에 그대로 적용할 수 없다.

NAS 재사용 분기의 full 검증은 가상 구성요소 바이트 대조로 표현했다. 운영용 full 검증 명령, 저장 매체 접근 및 실제 영수증 정규화는 별도 수용 검사 대상이다. 새 로컬 작업에서 CAS가 이미 색인되었다고만 보고하면 신규 성공을 거부한다. 기존 당일 로컬의 NAS 복구만 필요한 경우에는 후속 운영 상태 계약을 별도 설계한다.

운영 우회 경로는 구 native.v02/v042 감독자, 이전 OneShot의 수동 run, Gate의 직접 run, SelectiveSecureBackup의 직접 backup, NAS CAS의 직접 capture 및 별도 NAS 복제 도구다. 이들은 B4 감독자의 공통 잠금을 소유하지 않는다. 직접 진입을 제한하거나 같은 잠금 소유권 아래에 연결하기 전 운영 전환은 BLOCKED다. 자식이 감독자 잠금을 다시 획득하지 않도록 하고, 기존 내부 잠금의 획득 순서와 장애 시 해제를 확인한다.

B4는 고정 가상 작업 파일만 실행한다. Python 감사 훅과 경로 검사는 협력적인 후보 코드의 실행 경계다. OS 전체 권한 격리, 심볼릭 링크 교체 경쟁 및 임의 네이티브 코드 차단을 보증하지 않는다. 시험 프로세스 그룹 내 잔존을 검사하며 새 세션으로 이탈한 자식과 백업 중 강제 종료 시 매체 복구는 운영 전 별도 시험이 필요하다.
