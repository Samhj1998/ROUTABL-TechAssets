# MVL-01 명시적 후보 선택 인계

## CLI

```sh
/usr/bin/python3 -B mvl.py handoff initial --asset-id MVL-USER-R01-SELECTED-HANDOFF
/usr/bin/python3 -B mvl.py handoff final --asset-id MVL-USER-R01-SELECTED-HANDOFF --asset-id MVL-USER-SECOND
```

예시는 패치가 적용되고 해당 ID가 등록된 격리 환경을 전제로 한다. 옵션은 반복 가능하고 선택 순서대로 기존 고정 참조 뒤에 추가한다. `--asset-id`가 없는 초기·최종 인계는 기존과 동일하다.

## 설계와 재사용

- 기존 `register()`는 승인된 확장자·상대 경로와 `MVL-USER-...` ID 형식을 검사한 뒤 등록 레코드를 `mvl_sources`와 `docs`에 연결한다. 등록 방식과 DB 스키마를 그대로 사용한다.
- 선택은 읽기 전용 연결의 한 트랜잭션에서 `MVL/<ID>`로 정확히 조회한다. 일반 검색 결과는 SHA-256으로 그룹화되고 페이지 단위로 제한되므로 정확한 ID 선택에는 별도 조회가 적합하다. 일반 검색은 기존 v1.5를 사용한다.
- 등록 행과 대응하는 색인 행이 각각 유일해야 한다. 잘못된 등록 유형과 요청·저장 ID 불일치, 색인 해시·크기 불일치를 거부한다.
- 판본과 파일 메타데이터를 검사하고 `make_ref()`로 허용 필드만 재구성한다. `overlay_ref_allowed()`는 격리 폴더의 `incoming/` 바로 아래 허용 파일명으로 한정한다. 실제 파일이 로컬 해시 일치 상태일 때만 결과에 포함된다.
- `verify_source()`와 `read_evidence()`는 파일 존재·종류·해시·크기를 확인한다. 경로 구성요소에 심볼릭 링크가 있으면 안전하게 실패한다. 문서 바이트는 해시 계산에만 사용하고 출력은 메타데이터로 구성한다.
- 하나라도 실패하면 CLI는 종료 코드 1과 오류를 반환한다. 완전한 인계 문서가 만들어진 다음 한 번 출력하므로 일부 행만 인계되지 않는다.
- 이 검증은 등록·색인의 기대값과 생성 시점의 파일 일치를 확인한다. 등록·색인·파일 세 가지를 동시에 바꾸는 공격에 대한 서명 검증은 이 개선 범위 밖이다.

## 최소 반영과 재현

`SELECTED_HANDOFF.patch`의 변경 대상은 `mvl.py` 한 파일이다. 적용 전 기준 SHA-256은 `6aa94e2c46aea8b70313952dba7440c71696542d2fc64413b5cb7cb7f9b3b1b3`다. 패치로 재현한 후보 SHA-256은 `e8f3b458475e5d783e98bf0f2b1ebe6ccc2235a4355df70b44aea59ef1ab8fdd`다. `mvl_original.py`는 기준 비교용 사본이며 `mvl_provenance.py`와 v1.5 서비스는 시험용 원본 사본이다.

독립 수신 폴더에서는 다음 명령으로 합성 시험을 재현한다.

```sh
/usr/bin/shasum -a 256 -c SHA256SUMS
LC_ALL=en_US.UTF-8 /usr/bin/python3 -E -s -B -m unittest -v test_selected_handoff
```
