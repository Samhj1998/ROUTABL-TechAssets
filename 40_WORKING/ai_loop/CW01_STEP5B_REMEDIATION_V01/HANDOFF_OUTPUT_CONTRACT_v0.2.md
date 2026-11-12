# CW-01 인계 출력 계약 후보 v0.2

Step 5-B 검토본. CW-01 v1.0의 인계·승인 원칙을 구체화한다.

## 필수 필드

모든 레코드에 아래 키를 둔다. 확인할 수 없는 값은 JSON null 또는 표의 미확인으로 표시하고 이유를 적는다. 검증 대상, 시각, 수행자가 다른 경우 레코드를 분리한다.

| 필드 | 의미 |
|---|---|
| asset_id | 인계에서 정한 안정 식별자 |
| repository_root | 경로가 해석되는 저장소 기준점 |
| relative_path | 기준점에 대한 상대경로 |
| expected_sha256 | 승인된 인계·대장 등 비교 기준에서 받은 64자리 |
| observed_sha256 | 기재된 수행자가 원본 전체 바이트를 직접 계산한 64자리. 직접 계산이 없으면 null |
| verification_status | 아래 판정값 |
| verification_actor | 실제 검증 수행자와 역할·세션. 수신자와 후속 평가자를 구분 |
| evidence_source_type | REFERENCE_ONLY, DIRECT_TOOL_OUTPUT, USER_RELAYED_TOOL_OUTPUT, EVALUATION_REPORT 중 증거의 실제 수집 형태 |
| verification_method | 실제 도구·명령과 장치. 원본 바이트 계산과 문서 대조를 구분 |
| verified_at | 수행 시각과 시간대. 미수행·미확인은 null |
| evidence_location | 최초 근거 위치와 보존 사본 위치·SHA-256, 가능하면 메시지·도구 호출 식별자 및 연결된 평가 위치 |

원본 증거를 얻은 경로, 사본을 보존한 경로, 사본을 비교한 평가자를 각각 기록한다. USER_RELAYED_TOOL_OUTPUT은 수행자가 직접 계산한 도구 출력의 사용자 전달본이다. 평가자는 전달본을 대조한 행위만 자신의 수행으로 기록한다. EVALUATION_REPORT만 있으면 원격 원본 로그 확보를 주장하지 않는다.

| 상태 | 판정 |
|---|---|
| REFERENCE_REPRODUCED | 기대값과 경로를 재현했다. observed_sha256은 null |
| DIRECT_HASH_VERIFIED | 기재된 수행자의 실제 바이트 계산 근거가 있고 실측값이 기대값과 일치 |
| HASH_MISMATCH | 직접 계산값이 기대값과 불일치 |
| NOT_ACCESSIBLE | 지정 파일 또는 장치 접근 실패. 실측값은 null |
| NOT_TESTED | 실행하지 않았거나 실행 근거 부족. 확인되지 않은 실측값은 null |

검증 수행과 출처 유형은 별개 축이다. 수신자의 직접 계산을 전달본으로 평가한 경우 수행자·출처·보존 위치를 모두 기재한다. 해시 일치로 맥락 격리나 권한 차단을 추정하지 않는다.
