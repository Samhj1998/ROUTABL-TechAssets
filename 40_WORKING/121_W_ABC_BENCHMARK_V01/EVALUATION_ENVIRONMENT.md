# 평가 환경

| 항목 | 관측 |
|---|---|
| 지정 장치 | MacStudioui-MacStudio.local · c377300b-a710-43a6-8169-f17e87175403 |
| OS와 아키텍처 | macOS 27.2 arm64 |
| Python / SQLite | /usr/bin/python3 3.9.6 / SQLite 3.54.0 |
| DB 입력 | A 원본의 읽기 전용 로컬 백업 및 1/5/10배 합성 사본 |
| 캐시 | OS 페이지 캐시 강제 제거 없이 수행. 새 프로세스는 Python 초기화 비용을 별도로 관측 |
| 계측 | 단일 벤치마크 프로세스에서 연결 조건별 6순서 교차. 인덱스 및 A 원형 진단은 주 검색 계측 완료 후 수행 |
| HTTP | NOT_TESTED. API 함수 호출과 JSON 직렬화 시간으로 범위 제한 |

재현 스크립트 `code/core.py`, `code/functional.py`, `code/bench.py`, `code/index_trials.py`, `code/summary.py`, `code/addendum.py`. 모든 경로는 평가 폴더의 새 복제본에서 재현한다. 기존 증거의 스크립트/DB에 재실행하여 덮어쓰지 않는다.
