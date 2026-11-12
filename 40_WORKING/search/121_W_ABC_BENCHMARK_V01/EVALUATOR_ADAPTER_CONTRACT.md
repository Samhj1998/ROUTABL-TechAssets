# 평가 어댑터 계약

- A의 바이트 고정 운영 소스를 AST로 읽어 검색 함수 및 필요한 상수만 실행했다. 서비스 시작, 포트 리스닝, 운영 refresh는 호출하지 않았다. 운영 alias와 crosswalk는 A의 기존 정의와 기존 resolve_crosswalk를 같은 장치에서 읽기 전용으로 적용했다.
- B는 동결 SearchSnapshot 및 모듈 query를 호출했다. 별칭·검증 경로·분류 상수만 공통값으로 바인딩했다. C는 같은 DB와 설정을 동결 SearchEngine 생성자로 전달했다. 후보 파일의 바이트는 원본과 동일하다.
- A의 성능 계측용 sqlite3 연결 어댑터는 같은 SQL과 파라미터를 실행하고 A가 받는 행을 바꾸지 않는다. fetchall 계측으로 인해 약간의 런타임 차이가 생길 수 있으므로 A 원형의 새 연결은 별도 진단으로 표시한다. A 재사용 연결은 운영 A의 원형 동작을 의미하지 않는다.
- B 재사용은 검증한 DB 세대를 고정한 SearchSnapshot을 유지한다. C 재사용은 계속 열린 연결에서 schema_version/data_version 및 파일 inode를 점검하고 필요할 때 재연결한다. 갱신 시험은 같은 의미의 현재 세대 조회와 B의 이전 세대 스냅샷을 구분한다.
- 후보 감사에서는 B audit=True, C debug=True를 사용한다. 성능 시험은 두 디버그 옵션을 껐다. 오류 발생 시 C last_metrics를 읽지 않고 예외 분류와 외부 타이머만 남겼다. B 후보·LIKE 재검사는 같은 SQL 문장에 있어 시간 분리를 주장하지 않는다.
- MATCH 오류는 B SQLite authorizer의 MATCH 거부, C 인스턴스 MATCH 표현식의 구문 오류로 주입했다. 두 경우 모두 다음 A LIKE 경로는 정상 실행된다. 후보 알고리즘과 동결 파일에는 변경이 없다.
