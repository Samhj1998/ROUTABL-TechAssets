# MVL-01 사용 안내

Mac Studio의 터미널에서 다음 경로로 이동한다. 기본 검색과 인계 생성에는 서버나 별도 패키지가 필요 없다.

```sh
cd /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01
/usr/bin/python3 -B mvl.py check
/usr/bin/python3 -B mvl.py search 'TransportStatusPolicy.kt' --scope main
/usr/bin/python3 -B mvl.py search 'MVL01-FEEDBACK'
/usr/bin/python3 -B mvl.py handoff final
```

- `search`는 v1.5의 기존 검색·정렬·중복 묶음을 사용한다. 신규 격리 자산을 찾을 때는 기본 범위 `all`을 사용한다.
- `origin.source_path`는 검증한 원본 경로다. 중복 묶음의 대표 검색 경로와 다를 수 있다. `LOCAL_HASH_MATCH`는 로컬 파일의 현재 SHA-256·크기 일치를 뜻한다.
- `OFFICIAL_ROW`, `REGISTRY_DOCUMENT`, `PINNED_REFERENCE`, `ISOLATED_CANDIDATE`는 등록의 근거를 구분한다. CW-01 문서는 공식 원칙 문서이며 이 색인에서는 대장 행이 아닌 지정 원본으로 연결된다.
- 구 검색의 `status` 및 GitHub·NAS 필드는 이전 색인과 대장의 역사적 참조다. 이번 검증 결과는 `origin.status`에서 확인한다. 출처 버전이 원본에 명시되지 않은 경우 비워 둔다.
- 검증 불가나 불일치는 검색 결과에 상태로 남는다. 인계에 필요한 자산의 원본이 누락되거나 달라지면 인계 생성을 중단한다. 더 최신 대장이 등장하거나 핀이 달라져도 중단한다. 검토된 판본을 반영하려면 코드의 대장 핀과 실제 구조를 재검증한다.

## 신규 자료와 검증 결과 환류

1. 결과·시험·실패·해결 근거를 정리한 Markdown이나 텍스트를 이 폴더의 `incoming/`에 저장한다. 파일 이름은 영문·숫자·점·밑줄·하이픈을 사용한다. 고객정보나 인증 비밀이 없는 검토본을 사용한다.
2. 예를 들어 파일을 `incoming/settlement-review.md`로 저장했다면 다음처럼 등록하고 자산 ID로 검색한다.

```sh
/usr/bin/python3 -B mvl.py register MVL-USER-SETTLEMENT-REVIEW 1.0 incoming/settlement-review.md
/usr/bin/python3 -B mvl.py search MVL-USER-SETTLEMENT-REVIEW
```

3. 등록은 격리 SQLite에 ID와 경로·판본·해시 등 메타데이터를 추가한다. 변경판은 새 파일과 새 ID를 사용한다. 같은 ID와 같은 바이트로 반복 등록하면 기존 항목을 유지한다.
4. 사용자 추가 자료는 로컬 검색에 즉시 반영된다. 기본 인계의 전송 후보는 검토된 고정 목록이다. 실제 수신자에 사용자 추가 자료를 포함하려면 검색의 `origin`에서 필요한 메타데이터를 선택하고 전달 범위를 먼저 확인한다. 이미 검토된 MVL-01 환류는 `handoff final`로 다시 생성할 수 있다.

`check`는 격리 DB와 대장 핀을 확인한다. 문제가 있으면 해당 명령을 중단하고 터미널을 닫으면 된다. `Ctrl-C`로 실행 중인 CLI를 중단할 수 있다. 실행 중인 서버나 정기 작업은 없다. 배포 당시 해시 목록은 `SHA256SUMS`이며, 사용자 등록 후에는 격리 SQLite의 해시가 달라지는 것이 정상이다. 증거 기준판을 다시 비교할 때는 그 차이를 구분한다.

## 격리 시험 다시 실행

출시 당시 색인 상태에서 아래 명령을 사용할 수 있다. 최종 단계의 정확한 행 수 시험은 사용자 등록 이전의 색인 상태를 기준으로 한다.

```sh
/usr/bin/python3 -B test_mvl.py initial
/usr/bin/python3 -B test_mvl.py final
```
