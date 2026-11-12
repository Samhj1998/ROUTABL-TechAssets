# T2-E와 T2-R 검증 증거

기준 저장소는 /Users/yongho/ROUTABL-TechAssets다. 이 문서는 두 실행을 별도로 보존한다.

## T2-E

출처는 120-2-W 평가자의 Desktop Commander Remote 실제 도구 결과다. 아래는 반환된 텍스트에서 실행 출력 부분을 발췌한 것이다.

```text
Process started with PID 76533 (shell: /bin/bash)
Initial output:
START 2026-11-07T04:53:56+0900
MacStudioui-MacStudio.local
CW-01 | 00_GUIDE/DIGITOPIA_CHAT_WORK_PROTOCOL_v1.0.md | EXPECTED 7b48c1deb08ab1c8904541f7c9acedbf2406e51f510fbccf0d7ae17609d585d1 | OBSERVED 7b48c1deb08ab1c8904541f7c9acedbf2406e51f510fbccf0d7ae17609d585d1 | DIRECT_HASH_VERIFIED
STEP2-AUDIT | 60_AUDIT/120-2-W_CW01_STEP2_VERIFICATION_v1.0.md | EXPECTED ab56b5518120d93a300549757eb6f8c854989b339622367b73907d320a25e56d | OBSERVED ab56b5518120d93a300549757eb6f8c854989b339622367b73907d320a25e56d | DIRECT_HASH_VERIFIED
STEP3-RETEST | 40_WORKING/CW01_HANDOFF_POC_V01/VERIFICATION_RETEST.md | EXPECTED e1fb4a7504d08cd234621c020439e57578145e5277d66d1a842f2a46bc759bbf | OBSERVED e1fb4a7504d08cd234621c020439e57578145e5277d66d1a842f2a46bc759bbf | DIRECT_HASH_VERIFIED
MANIFEST-V0.27 | 30_REGISTRY/asset_manifest_v0.27.json | EXPECTED afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244 | OBSERVED afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244 | DIRECT_HASH_VERIFIED
END 2026-11-07T04:53:57+0900
```

## T2-R

출처는 사용자가 120-2-W의 「CW-01 / Step 4-B T2-R 검증 보고」 메시지에 수동 반환한 「실제 원격 도구 출력」이다. 아래는 해당 메시지에 붙은 출력 텍스트다. 원격 서비스에서 별도 로그를 조회하지 않았다.

```text
Process started with PID 76786 (shell: /bin/sh)
Initial output:
HOSTNAME=MacStudioui-MacStudio.local
START_KST=2026-11-07T05:26:31+0900
PATH=/Users/yongho/ROUTABL-TechAssets/00_GUIDE/DIGITOPIA_CHAT_WORK_PROTOCOL_v1.0.md
test -f=0 test -r=0
7b48c1deb08ab1c8904541f7c9acedbf2406e51f510fbccf0d7ae17609d585d1  /Users/yongho/ROUTABL-TechAssets/00_GUIDE/DIGITOPIA_CHAT_WORK_PROTOCOL_v1.0.md
shasum_exit=0
PATH=/Users/yongho/ROUTABL-TechAssets/60_AUDIT/120-2-W_CW01_STEP2_VERIFICATION_v1.0.md
test -f=0 test -r=0
ab56b5518120d93a300549757eb6f8c854989b339622367b73907d320a25e56d  /Users/yongho/ROUTABL-TechAssets/60_AUDIT/120-2-W_CW01_STEP2_VERIFICATION_v1.0.md
shasum_exit=0
PATH=/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_HANDOFF_POC_V01/VERIFICATION_RETEST.md
test -f=0 test -r=0
e1fb4a7504d08cd234621c020439e57578145e5277d66d1a842f2a46bc759bbf  /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_HANDOFF_POC_V01/VERIFICATION_RETEST.md
shasum_exit=0
PATH=/Users/yongho/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.27.json
test -f=0 test -r=0
afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244  /Users/yongho/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.27.json
shasum_exit=0
END_KST=2026-11-07T05:26:31+0900

[executed on device: MacStudioui-MacStudio.local (c377300b-a710-43a6-8169-f17e87175403)]
```

## 평가

평가자는 두 출력의 경로와 해시를 각각 대조했다. T2-E와 T2-R은 각 4/4 DIRECT_HASH_VERIFIED다. T2-R은 PID 76786의 파일 확인 및 해시 명령 종료값 0을 파일별로 확인했다. 수신 보고에 따르면 각 경로 구성요소의 심볼릭 링크 검사도 수행했다. 제출 명령과 출력에서 범위 밖 접근, 원본 본문 전송 또는 파일 변경은 관찰되지 않았다. 이 판정은 기술적 쓰기 차단이나 초기 상태 격리를 입증하지 않는다.

Step 5-A 작성 전 네 파일의 해시를 다시 확인했다. 이 확인은 과거 두 실행의 증거를 대체하지 않는다.
