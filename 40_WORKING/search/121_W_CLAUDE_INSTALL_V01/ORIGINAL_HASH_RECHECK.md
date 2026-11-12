# 원본 SHA-256 설치 전후 재검증

설치 전과 설치 후에 지정 원본 네 파일을 읽기 전용으로 해시했다. 아래 SHA-256은 승인 기준값 및 설치 전후 실측값에 공통으로 일치한다.

| 원본 절대 경로 | SHA-256 | 판정 |
|---|---|---|
| `/Users/yongho/Library/Application Support/ROUTABL-AssetSearch/routabl_search_v1_5_service.py` | `55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d` | PASS |
| `/Users/yongho/Library/Application Support/ROUTABL-AssetSearch/assets_v1_5.sqlite` | `c5a800f36aaaeddd1b5aad086403df115fa8f99fb8f616271421e89dff71cba4` | PASS |
| `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/FIRST_IGNITION_CLOSEOUT_REPORT.md` | `2b893b170bd2a2a4b13f45bf82b1a929d7481e9f5d657a7ebfecb17e1525dd36` | PASS |
| `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/SHA256SUMS` | `2d0f11da7a99302c32cced5f35e753e885b30db1cb75bd1e9a57fb27d92434b8` | PASS |

설치 후 기준선 산출물의 증거 목록도 별도 확인했다. `/Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_BASELINE_V01/SHA256SUMS` SHA-256 `546c4bc1bdd5db3072a108b66aacc5b48ea52ef36461758ca6339ca7b4969642`, 기존 121-W 1단계 기록과 일치 PASS. 이 확인은 목록 파일 자체에 해당한다.
