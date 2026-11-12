# 120-2-W Step 2 CW-01 생성·검증 감사 보고서

- 검증 시각 (KST) 2026-11-07T00:02:11+09:00
- 대상 MacStudioui-MacStudio.local
- 기준 경로 `/Users/yongho/ROUTABL-TechAssets`
- 관리 ID `CW-01`
- 등록 후보 `ASSET-120-CW01-PROTOCOL-V1.0` (대장 미등록)

| 검증 항목 | 결과 | 증거 |
|---|---|---|
| 읽기 전용 사전 실사 | PASS | 기술자산 루트, 00_GUIDE, 30_REGISTRY, 60_AUDIT 확인 |
| 신규 문서 생성 및 읽기 대조 | PASS | `/Users/yongho/ROUTABL-TechAssets/00_GUIDE/DIGITOPIA_CHAT_WORK_PROTOCOL_v1.0.md`, SHA-256 `7b48c1deb08ab1c8904541f7c9acedbf2406e51f510fbccf0d7ae17609d585d1` |
| 공식 규칙 전문 | PASS | 규범 구역의 UTF-8 바이트가 사용자 제공 전문과 일치. 구역 SHA-256 `6ca56cf6062420eb16967252aaaaeba5e4ce0f170a512b16840196adfe845f23` |
| 최신 대장 | PASS | 버전 번호 기준 v0.27, 2026-11-06 제공 해시 일치 |
| 기존 원칙 및 대장 | PASS | 신규 문서 생성 전후 SHA-256 일치 |

| 파일 | 작성 전 SHA-256 | 작성 후 SHA-256 |
|---|---|---|
| `00_GUIDE/ROUTABL_3TIER_ASSET_PROTECTION_AND_RESTORATION_PRINCIPLE_TI01_v1.0_20261106.md` | `21833f37c1c0e686743dca77a341577db9b2f0e97d93a8773a25fc8955711132` | `21833f37c1c0e686743dca77a341577db9b2f0e97d93a8773a25fc8955711132` |
| `00_GUIDE/ROUTABL_VERSION_INDEPENDENCE_PRINCIPLE_v1.0_20261106.md` | `86c79cd8cc11aac2aed2054c9f92ad445050ce5cfb6f17f17b355f75b4c4eb54` | `86c79cd8cc11aac2aed2054c9f92ad445050ce5cfb6f17f17b355f75b4c4eb54` |
| `30_REGISTRY/asset_manifest_v0.27.json` | `afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244` | `afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244` |

실행은 승인된 두 신규 파일 생성으로 제한했다. 기존 파일과 외부 시스템의 전수 감사는 이번 검증 범위 밖이다.

## 미실행·미검증

- 운영 자산대장 반영, Step 3 구현, Step 4 운영 검증, Step 5 환류는 미실행이다.
- 신규 문서의 SSD·NAS 백업 반영과 실제 복원, 별도 AI별 적용본 대조는 미검증이다.
- 다음 단계는 120-2 Chat에서 Step 3 표준 인계 기록 설계를 검토하는 것이다.
