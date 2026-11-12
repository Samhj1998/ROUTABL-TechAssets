# 121-W Step 4-B 종료

대상 MacStudioui-MacStudio.local, `c377300b-a710-43a6-8169-f17e87175403`. macOS 27.2 arm64, Python 3.9.6, SQLite 3.54.0. C는 Claude Code Homebrew stable 2.1.309, 바이너리 SHA `5eadc0009cdcdbc0d06e58110d7b2baf88ced6088b1c33a60a21217fe410619c`를 확인했다.

| 항목 | 판정 | 근거 |
|---|---|---|
| 동일 입력 7건 × 2, 공통 지시문 | PASS | 사전/사후 해시 일치. 공통 지시문 SHA `e22dd54c0a9047c5d5e72f282d98bcc75ba8f28dfa9d854c672ebbd4899402c0` |
| 평가 코호트 사전 동결 | PASS | 13:14:36 KST. 혼합 50건 1/50, 개발 30·보류 20·운영 9 별도. 선택적 40, 결과 없음 10, 중간·다건 0. 평가자 목록 SHA `a5aa8fac99eaddf410a89fa7a7b0a05bdd9c9e298473557b1dd01efe9ec43efc` |
| B 공개 개발시험·동결 | PASS | 30/30 전체 객체 일치, 후보 누락 0, 경계 36/36. B 자체 체크섬 10/10, 전체 36개 파일 평가자 동결 |
| B 작업 DB 위치 규약 | FAIL | 합성 작업 DB 21건이 tests 대신 output 아래 생성. 최초 증거를 그대로 보존. 재현은 승인된 tests의 새 복사본으로 수행 |
| C 공개 개발시험·동결 | PASS | 개발 30질의, 범위·페이지 포함 510개 반환 객체 비교 차이 0, 후보 누락 0, T01~T11 통과. 자체 체크섬 12/12, 전체 52개 파일 평가자 동결 |
| C 실행 완결 | PASS | 첫 1,000초 종료(143) 후 기존 소스·시험 코드 바이트를 보존하고 보고서·체크섬만 별도 실행으로 완료(0) |
| 운영·고정 증거 보존 | PASS | 운영 v1.5 소스/DB, B/C 분석 원본, 120-2 MVL-01 보고서·목록, 기준선 22개 및 Step 4-A 25개 해시 확인 |
| 후속 공통 평가 | NOT_TESTED | 운영 9질의·보류 20질의 후보 실행/채점, 공식 1/5/10배 비교, 운영 적용·복구 미실행 |

합성 1,230행에서 선택적 1~12, 중간 13~245, 다건 246 이상, 결과 없음 0으로 동결했다. 혼합 50건에서 다건/짧은 대표 질의가 부족해 보조 경계 7건을 기존 목록과 분리했다. 이 정확한 보조 정의는 C 시작 후 공식 비교 전에 추가 동결했으며 기존 코호트·가중치는 유지했다. 보조 SHA `ddf5a17d75f9693ec2a998f477a0e4e496929a971c668afb7009fd79aef1da52`.

B A/B 공개 Recall/Precision/MRR/nDCG@10 각 0.800/0.160/0.800/0.800. 초성 6건이 두 쪽 공통 미달. C는 공개 qrels 동등성을 기록했다. C 개발 계측에는 연결 조건이 다른 A/C 계측이 있어 채택 자료로 사용하지 않는다. B의 메모리 백업·FTS 검사와 C 세대검증은 정식 평가에서 새 연결과 재사용 연결로 나눠 측정한다.

## 121 Chat 인계문

```text
121 Chat / Step 4-B 완료 검토 및 Step 4-C 승인 범위 결정

MacStudioui-MacStudio.local (c377300b-a710-43a6-8169-f17e87175403)에서 B/C 최초 구현을 독립 완료하고 동결했습니다. 공통 7개 입력을 사전/사후 검증했습니다. 공통 구현 지시문 SHA e22dd54c0a9047c5d5e72f282d98bcc75ba8f28dfa9d854c672ebbd4899402c0.

B /Users/yongho/121_CHATGPT_B_V01/implementation/
B 후보 src/search_b.py SHA f46f64e2479a331c6bd6822f7b0b41af2fbceeab801bb27ad679dce108d1950d
B output/SHA256SUMS SHA 70ec00dfe861be12aa075ec0011dd9bab58dafeae1d6f3829f9b441d3f795a28
공개 30/30, 누락 0, 경계 36/36. 체크섬 10/10. 작업 DB 21건을 output에 둔 위치 규약 FAIL을 기록하고 최초 상태를 보존했습니다. 재현은 tests의 별도 합성 사본으로 진행합니다.

C /Users/yongho/121_CLAUDE_ISOLATED_V01/implementation/
C 후보 src/asset_search_fts.py SHA 0a33cd62f47d530813ba23e30eb0616945469a42ffba105714b02a827b576a3b
C output/SHA256SUMS SHA aa3d4118bbe6ad85ee627230af3d39635bc9a7397995fedfcfc85a0565c9b16e
공개 30질의의 scope·페이지 포함 510회 차이 0, 후보 누락 0, T01~T11 PASS. 체크섬 12/12. 첫 CLI 시간 상한 뒤 C가 소스·시험을 보존한 상태에서 문서만 완성했습니다.

증거 /Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_ABC_IMPLEMENTATION_V01/
전체 파일은 SHA256SUMS, 후보별 경로·해시는 B_IMPLEMENTATION_FREEZE_MANIFEST.md 및 C_IMPLEMENTATION_FREEZE_MANIFEST.md, 후속 요청은 STEP4C_APPROVAL_REQUEST.md를 확인해 주세요.
평가자 코호트 SHA a5aa8fac99eaddf410a89fa7a7b0a05bdd9c9e298473557b1dd01efe9ec43efc. 합성 50건 각 1/50, 선택적 40·결과 없음 10. 다건·짧은·폴백은 별도 보조 정의이며 혼합 50에 포함하지 않습니다.

Step 4-C에서만 동일 장치·동일 데이터로 운영 9/9, 개발 30·보류 20 회귀 0, 정확도 비악화, 후보 누락 0, 갱신 정합성을 검증하도록 승인해 주세요. 이후 1/5/10배에서 혼합 p95 20%·선택적 30% 개선, 짧은·다건·폴백 악화 각 10% 이내, 색인 각 10% 원칙, 공간 5%를 적용합니다. 운영 소스·DB·서비스·공식 대장 변경과 운영 배포는 이 승인에서 제외합니다.
```
