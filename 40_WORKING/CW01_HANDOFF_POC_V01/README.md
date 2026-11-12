# CW-01 표준 인계 기록 실증판 v0.1

기준 데이터는 두 모의 JSON이다. `schema.json`은 120-2와 120-2-W의 양방향 필드와 검증 상태를 정의한다. `handoff.py`는 표준 라이브러리로 이 스키마에 쓰인 키워드를 검사하고 Markdown을 생성한다. 기록 ID는 모의 전용이다. `historical`은 참조 자산에 기록된 실제 사실, `simulated`는 가상 사례를 나타낸다.

기존 생성물 대조
```sh
python3 -B handoff.py verify chat_to_work.json work_to_chat.json
python3 -B verify_poc.py
```

신규 모의 JSON은 이 폴더에서 `render`로 동일 이름의 Markdown을 생성할 수 있다. 이미 있는 Markdown은 덮어쓰지 않는다. 중복 ID 검사는 명령에 함께 전달한 JSON 범위에서 수행한다.

실행 허용 판정은 로컬 시험 행동 한 종류에만 적용된다. 판정이 PASS여도 실행 기능은 없다. 외부 전송 요청은 전부 차단한다. 제한 등급과 일부 자격증명 표식을 출력 전에 차단한다. 자유 텍스트의 모든 민감 정보를 식별하는 기능은 포함하지 않는다. 자동 연결, 실제 승인 인증, ID 발급, 봉인, 외부 전송, 운영 대장 등록 기능은 포함하지 않는다.
