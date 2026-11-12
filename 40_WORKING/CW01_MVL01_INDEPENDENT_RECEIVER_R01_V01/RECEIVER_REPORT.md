# CW-01 MVL-01 독립 수신 검증 보고서

독립 수신 개발 과제 **PASS**. 전체 First Ignition 판정은 120-2-W의 독립 재검증과 후보 등록·재검색·재인계 이후 갱신한다.

## 수신 환경과 승인 경계

- MacStudioui-MacStudio.local · 장치 ID `c377300b-a710-43a6-8169-f17e87175403` · Darwin arm64 · Apple Python 3.9.6.
- 읽기 원본 `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/`. 아래 9개 파일의 바이트 SHA-256을 직접 산출했다. 신규 작업 폴더를 배타적으로 생성한 후 모든 쓰기와 시험을 `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_INDEPENDENT_RECEIVER_R01_V01/`로 제한했다.
- 인계 문서 두 건을 먼저 확인했다. 이어 승인된 코드와 실행 안내·이전 결과를 검토했다. 기존 결과의 PASS는 역사적 기록으로만 사용했다.
- 운영 검색·DB, 기존 MVL-01의 SQLite, 공식 대장 전문, 그 밖의 기술자산, Firebase, NAS, 백업·복원, 외부 전송 및 Step 5-C는 이 작업 범위 밖이다.

| 승인 파일 | 기대 SHA-256 = 직접 실측 SHA-256 | 작업 전후 |
| --- | --- | --- |
| `HANDOFF_FINAL.md` | `470db7b07e2148352c42aad81e8610943e97aae4a940c0d9c6aa864be5845acb` | 일치 |
| `INDEPENDENT_RECEIVER_PROMPT.md` | `8c05c61c16fa376825ab836f9dc1f3f445b2a9adcf9340d6f6db0ed4eec9a5e5` | 일치 |
| `mvl.py` | `6aa94e2c46aea8b70313952dba7440c71696542d2fc64413b5cb7cb7f9b3b1b3` | 일치 |
| `mvl_provenance.py` | `58cfd63bde15618a5d3e870a3080e1d3ce41e62301fa257865fdcf9cff294e6c` | 일치 |
| `routabl_search_v1_5_service.py` | `f391044addc200f7c2cd70cb68163e913751c619b5a9b8ff42afc824e08885fc` | 일치 |
| `test_mvl.py` | `09541d61260f5ec8f4272b3660ef866f3f27e01f85434695c30bf314d8bed0f6` | 일치 |
| `FEEDBACK_CANDIDATE.md` | `04402d26ebc08985acd63a49bba77064deb315c02b994197165adef8d8d861b3` | 일치 |
| `RUN_GUIDE.md` | `286b3afb413997f9561652f074b270988b45352bc7939f428bdb02f1bb8ad868` | 일치 |
| `TEST_RESULTS_FINAL.json` | `ad66ccbd3ee5eb5b6daa588de3b5c0d3c120fb18b4a72285f9c1f2960446ca92` | 일치 |

## 인계 문맥 복원

기존 MVL-01은 v1.5의 한국어 별칭·검색 SQL·순위·SHA 기준 중복 묶음을 재사용한다. 인계 문서에는 격리판의 대장 v0.27 선택, v0.6과 v0.27의 두 출처 연결 일치, 검색 결과에서 기대값과 원본 바이트 실측값 분리, 환류 후보의 재검색이 기록돼 있다. 이번 수신 과제는 이 구조를 사용해 등록 후보를 명시적으로 인계하는 기능을 만들고 독립 시험으로 검증하는 것이다. CW-01의 ID·경로·해시 인계 구조와 AF-01의 로컬 접근 방식을 반영했다.

| 인계에 기록된 자산 ID | 문서상 기대 SHA-256 | 문서상 등록 구분 | 이번 세션의 증거 |
| --- | --- | --- | --- |
| ASSET-SEARCH-V15-SERVICE | `55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d` | OFFICIAL_ROW | 인계 문서의 기록. 해당 원본은 미검증. |
| MVL01-REGISTRY | `afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244` | REGISTRY_DOCUMENT | 인계 문서의 기록. 해당 원본은 미검증. |
| AF-01 | `13eadac676aed2e97c0486edbed67c9db85a1d693545de80db209830614805d5` | PINNED_REFERENCE | 인계 문서의 기록. 해당 원본은 미검증. |
| CW-01 | `7b48c1deb08ab1c8904541f7c9acedbf2406e51f510fbccf0d7ae17609d585d1` | PINNED_REFERENCE | 인계 문서의 기록. 해당 원본은 미검증. |
| MVL01-CW-POC | `e1fb4a7504d08cd234621c020439e57578145e5277d66d1a842f2a46bc759bbf` | PINNED_REFERENCE | 인계 문서의 기록. 해당 원본은 미검증. |
| MVL01-CW-COLD | `bf8a093caf412b45f8400efda3b9a0bb6fea26b7af0b0378b3f648ea60eed688` | PINNED_REFERENCE | 인계 문서의 기록. 해당 원본은 미검증. |
| MVL01-CW-FEEDBACK | `c5735b796213cb93f718167ed5a2b4006b6a1816991a6d7eb71520053666e455` | PINNED_REFERENCE | 인계 문서의 기록. 해당 원본은 미검증. |
| MVL01-FEEDBACK | `04402d26ebc08985acd63a49bba77064deb315c02b994197165adef8d8d861b3` | ISOLATED_CANDIDATE | 승인 파일 직접 해시 일치. 실제 색인 행은 미검증. |

운영 v1.5 원본과 승인된 격리 v1.5 사본은 서로 다른 파일이다. 운영 원본에 대한 인계 문서의 해시를 격리 사본의 실측으로 대체하지 않았다. `FEEDBACK_CANDIDATE.md`는 승인 범위에 들어 직접 해시를 확인했으며 기존 DB의 등록 여부는 인계 문서의 기록으로 구분했다.

## 실제 개발 활용

원래 `mvl.py`의 `register()`와 `upsert()`는 `MVL/<ID>`로 등록 메타데이터와 문서 색인을 연결한다. `package()`는 `REFERENCES` 고정 목록 및 final의 `MVL01-FEEDBACK`을 기존 `lookup()`으로 읽는다. `RUN_GUIDE.md`는 사용자 추가 자료의 수동 메타데이터 전달을 설명한다. 이 접점에 반복 가능한 `--asset-id`를 추가했다.

선택 후보는 읽기 전용 SQLite에서 정확한 ID로 조회한다. 등록 ID·유형·판본·경로·해시·크기와 색인 일치를 확인한 다음 기존 `overlay_ref_allowed()`, `make_ref()`, `verify_source()`를 재사용한다. `verify_source()`는 기존 `read_evidence()`에서 파일과 경로 구성요소의 링크를 따라가지 않고 파일 바이트와 크기를 확인한다. 응답은 등록 메타데이터에서 허용 필드만 재구성하고, 선택한 자산 하나라도 검증에 실패하면 인계 문서 출력 전체를 중단한다.

## 시험과 원본 불변성

신규 폴더에서 실행했다.

```sh
LC_ALL=en_US.UTF-8 /usr/bin/python3 -E -s -B -m unittest -v test_selected_handoff
/usr/bin/shasum -a 256 -c SHA256SUMS
```

| 판정 | 검증 항목 |
| --- | --- |
| PASS | 합성 후보 등록 뒤 정상 인계. CLI Markdown에 지정 ID·원본 경로·판본·기대/실측 해시·등록 유형·검증 상태가 정확히 표시됨. 구조화 결과에는 크기 포함. |
| PASS | 동일 SHA의 서로 다른 ID 두 개를 요청 순서대로 인계. 실제 v1.5 검색은 같은 해시의 검색 결과를 한 그룹으로 묶음. |
| PASS | 미등록 ID, 잘못된 ID, 중복 선택, 중복 색인, 색인만 있는 행, 등록 ID 바꿔치기, 비후보 등록 유형, 잘못된 판본을 거부. |
| PASS | 파일 누락, 같은 크기의 파일 변조, 파일/부모 디렉터리 심볼릭 링크, 경로 이탈·상대 경로, 색인 누락·해시 불일치를 거부. |
| PASS | 선택 실패 시 종료 코드 1과 빈 표준 출력. 원문과 임의 JSON 필드 미포함. SQLite 읽기 전용 쓰기 거부 및 정상 인계 전후 합성 DB 바이트 일치. |
| PASS | 합성 환경에서 원본 CLI와 수정 CLI의 기본 initial/final 인계 전체 문구 및 패키지 구조가 일치. 검색 4개 사례의 전체 결과 일치. |
| PASS | 후보 코드 시험 20건 통과, 종료 코드 0. 패치를 원본 사본에 적용해 수정 코드와 바이트 단위 일치. 승인 원본 9개 전후 해시 일치. |
| NOT_TESTED | 실제 MVL-01 DB의 전체 검색 회귀, 공식 대장과 실제 교차 연결 검증, 실제 환경에서 후보 등록·재검색·재인계 및 운영 원본의 바이트 비교. |

첫 시험에서는 합성 대장 스텁에 `provenance_crosswalk` 키를 누락해 20건 모두 초기화 단계에서 종료했다. 스텁에 빈 목록을 추가한 뒤 후보 코드 변경 없이 재실행했고 20건 모두 통과했다. 최초 실패 로그는 `TEST_RESULTS_ATTEMPT_01.txt`, 통과 로그는 `TEST_RESULTS.txt`에 보존했다. 테스트는 합성 SQLite와 고정 참조 7개, 합성 환류 후보, 합성 v1.4 import 스텁을 사용했다. v1.5 검색 및 원본 검증에는 승인된 원본 사본을 사용했다.

원본 불변성의 바이트 확인 범위는 승인된 9개 파일이다. 운영 DB와 다른 원본은 읽거나 쓰지 않았으며, 해시 비교의 범위에 포함하지 않았다.

## 환류에 전달할 자료

이 폴더의 `SELECTED_HANDOFF.patch`, `RECEIVER_REPORT.md`, `SELECTED_HANDOFF_DESIGN.md`, `test_selected_handoff.py`, `TEST_RESULTS.txt`, `VERIFICATION.txt`, `INPUT_SHA256.json`, `SHA256SUMS`를 함께 검토한다. `SHA256SUMS`는 자체 파일을 제외한 산출물의 해시 목록이다.

120-2-W는 먼저 산출물 해시를 대조하고 위 시험을 재실행한다. 별도로 승인된 격리 적용본에서 `mvl.py`의 원본 핀을 확인하고 패치를 적용한다. 검토한 요약 문서 하나를 `MVL-USER-R01-SELECTED-HANDOFF`로 등록한 뒤 해당 ID를 재검색하고 파일 해시를 독립 계산한다. 그다음 `handoff final --asset-id MVL-USER-R01-SELECTED-HANDOFF`에서 ID·경로·판본·등록 구분·해시·상태를 대조한다. `handoff final`에는 그 ID가 없는지 비교한다. 이전 120-2-W 결과와 독립 수신 결과를 분리해 기록한다.
