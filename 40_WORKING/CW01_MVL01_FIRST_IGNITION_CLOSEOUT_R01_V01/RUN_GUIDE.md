# MVL-01 Closeout 재실행 안내

Mac Studio 터미널에서 아래 명령을 실행한다. 증거를 보존하려면 출력을 화면에서 확인한다.

    cd '/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01'
    /usr/bin/shasum -a 256 -c SHA256SUMS
    /usr/bin/python3 -E -s -B scope_runner.py mvl.py check
    /usr/bin/python3 -E -s -B scope_runner.py mvl.py handoff initial
    /usr/bin/python3 -E -s -B scope_runner.py mvl.py search MVL-USER-R01-SELECTED-HANDOFF
    /usr/bin/python3 -E -s -B scope_runner.py mvl.py handoff final
    /usr/bin/python3 -E -s -B scope_runner.py mvl.py handoff final --asset-id MVL-USER-R01-SELECTED-HANDOFF

기대 결과는 기본 initial 7건, 기본 final 8건, 선택 final 9건이다. 선택한 ID는 9번째 행에 한 번 나온다.
대상 원본을 읽을 수 없거나 SHA-256이 바뀌면 인계가 실패한다. 승인된 경로와 해당 자산의 기대 해시를 먼저 확인한다.
위 경로 제한 러너는 고정 참조 일곱 파일과 격리 문서 두 개만 원본 바이트 검증에 사용하고, SQLite 접속은 이 폴더의 DB로 제한한다. 운영 서비스 파일 접근은 승인된 SHA-256 계산 범위에 따른다.

이 폴더의 데이터와 해시 목록은 검증 결과다. 재등록이나 경로 정합화 실험은 별도로 승인받은 새 격리 폴더에서 실행한다. 이미 등록된 ID를 재등록할 필요는 없다.
