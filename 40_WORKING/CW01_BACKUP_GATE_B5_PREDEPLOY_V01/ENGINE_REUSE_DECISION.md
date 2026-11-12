# 기존 엔진 동일 바이트 재사용 판정

| 엔진 | 실측 SHA-256 | 판정 |
| --- | --- | --- |
| ROUTABL_HeadlessDailyGate_v0_3.py | 4992b2213bf2598c55a6ab68dd5bf35c501258d47e1e4780765c2a67343a3ce5 | 조건부 재사용. READY와 별도 SUCCESS, ALREADY_RUNNING 및 SKIPPED를 분리하고 selector와 Gate의 경로·락을 함께 핀한다. Gate check를 읽기 전용으로 가정하지 않는다. |
| ROUTABL_SelectiveSecureBackup_v2_1.py | f365dfec0b0053f5c124a7440e5fe0bdcf8ccef0b74b639a8b3473288b42186c | 조건부 재사용. 숫자 최신 대장, 등록 원본 크기·해시, 프로젝트/관리 포함 및 제외 정책을 보존한다. 원본 영수증을 닫기 전에 봉인한 증거를 안전하게 내보낼 수 없으면 신규 판본이 필요하다. 현재 선택 목록은 재실측하지 않았다. |
| ROUTABL_NAS_ContentAwareBackup_v0_2.py | fa370842507ae0afb1e11ede46d1a0f72ab4736c60329c8aa18f94c797794631 | 조건부 재사용. 신규 INCREMENTAL_SNAPSHOT_VERIFIED와 SNAPSHOT_ALREADY_INDEXED를 구분한다. 대상 CAS만 고정해 전체 참조를 검증하고 결과를 바이트에 묶을 수 없는 경우 별도 증거 어댑터 또는 신규 판본이 필요하다. |

실제 엔진 실행 호환성, 저장 매체 쓰기 자격 및 우회 차단은 NOT_VERIFIED다. 기존 코드가 독점 매체 접근을 전제로 하는 동안 운영 전환은 BLOCKED다. 격리 B4 어댑터는 정규화된 가상 영수증용이다. B5 정규화기는 실제 메타데이터 구조를 읽는 후보이고 운영 실행기 교체본은 아니다.
