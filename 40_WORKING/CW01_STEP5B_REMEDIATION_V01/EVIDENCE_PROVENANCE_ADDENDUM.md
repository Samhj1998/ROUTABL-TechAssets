# CW-01 T2 증거 계보 보완

기준 저장소는 /Users/yongho/ROUTABL-TechAssets다. 기존 EVIDENCE_LEDGER.json과 평가 점수는 유지한다.

## T2-E

- 수행자는 기존 120-2-W 평가자다. Desktop Commander Remote의 도구 응답이 120-2-W의 Step 4-B T2-E 실행에 남아 있다.
- MacStudioui-MacStudio.local, 장치 ID c377300b-a710-43a6-8169-f17e87175403, 원격 PID 76533, 2026-11-07 04:53:56–04:53:57 KST.
- test -f, test -r 후 /usr/bin/shasum -a 256으로 각 파일을 직접 계산했다. 4/4 일치. 출처 유형은 DIRECT_TOOL_OUTPUT이다.
- 보존 사본은 40_WORKING/CW01_STEP5_FEEDBACK_V01/T2_EVIDENCE.md의 T2-E 절이다. 채팅 도구 결과의 실행 출력 발췌를 보존했다.

## T2-R

- 수행자는 별도 Work 수신자(수신 보고 기준)다. 사용자가 「CW-01 / Step 4-B T2-R 검증 보고」로 실행 명령, 원격 도구 출력 텍스트와 자기 보고를 120-2-W에 수동 반환했다.
- Desktop Commander Remote, MacStudioui-MacStudio.local, 장치 ID c377300b-a710-43a6-8169-f17e87175403, 원격 PID 76786, 2026-11-07 05:26:31 KST.
- 제출 명령은 경로 구성요소의 심볼릭 링크 검사, test -f, test -r, /usr/bin/shasum -a 256을 사용했다. 반환 출력의 네 파일은 test -f=0, test -r=0, shasum_exit=0이었다.
- 출처 유형은 USER_RELAYED_TOOL_OUTPUT이다. 보존 사본은 위 T2_EVIDENCE.md의 T2-R 절이다. 원격 서비스 독립 로그는 미확보다.
- 평가자는 120-2-W다. 후속 「120-2-W 평가 결과」에서 반환 텍스트의 경로와 계산값을 승인 목록에 대조해 4/4를 인정했다. 평가는 EVALUATION_REPORT로 구분하며 별도 원격 계산에 해당하지 않는다.

## 보존 및 재확인

T2_EVIDENCE.md SHA-256은 ccf80195519741ce1385009c36843aa70472f61d969ce06a491fc1f59080d9dc다. EVIDENCE_LEDGER.json SHA-256은 f72492a155455dffbb2ca3ac67b5de7845de28440002cd4622008443ef8455e2다.

두 실행의 대상은 CW-01 공식 문서, Step 2 독립 감사, Step 3 최종 감사, 자산대장 v0.27이다. 상대경로와 기대·실측 해시 전체는 위 증거 원장과 보존 사본에서 재확인할 수 있다. 현재 단계에서는 두 보존 블록의 경로·해시·시각과 채팅에 남은 해당 출력을 대조했다. T2-R의 초기 맥락 격리와 기술적 쓰기 차단은 미검증 상태로 유지한다.
