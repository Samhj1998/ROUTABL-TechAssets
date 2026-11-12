# C 최초 구현 동결

구현 루트 `/Users/yongho/121_CLAUDE_ISOLATED_V01/implementation/`. Mac Studio에서 C가 작성한 체크섬을 `/usr/bin/shasum -a 256 -c output/SHA256SUMS`로 검증했다. 종료 0, 12/12 일치. 평가자 전체 파일 인벤토리는 `C_FREEZE_ARTIFACTS.json` SHA `61d8fb55acf233eab18660325f9664e6d9aa55b52caf982e62d2b3cd64b17cf4`. 작업 DB·실패 기록을 포함한 52개 파일을 0400, 산출물 하위 디렉터리를 0500으로 동결했다.

| 상대 경로 | SHA-256 |
|---|---|
| src/asset_search_fts.py | `0a33cd62f47d530813ba23e30eb0616945469a42ffba105714b02a827b576a3b` |
| tests/run_dev_tests.py | `8fa8f69d7263ec09852fb0dc2c02a9ee84f12f9b00b05fa77fdffc830139337e` |
| output/IMPLEMENTATION_REPORT.md | `8431ec8183698b6d2581c8aa53b7fc0e05f4c55c8dfdc4818f0ebc4877207760` |
| output/DEV_TEST_REPORT.md | `39c1143f78ec2a951ebd41c6185678badb54ac7c86bcc838bd27d7d59361ffee` |
| output/CHANGE_MANIFEST.md | `9182b1b1fdb043a5efa3e20861e7b1519a7ce58258338bed0f14d166187f6fe4` |
| output/runs/run_20261108T043152Z.json | `1e6ff145397f9e7a8075cffc5ae2b4f63e6f167e84810b4e3e7b52ccc0314408` |
| output/SHA256SUMS | `aa3d4118bbe6ad85ee627230af3d39635bc9a7397995fedfcfc85a0565c9b16e` |

최종 로그의 소스/시험 SHA와 실제 동결 파일 일치. 공개 30질의, scope·페이지 변형 포함 전체 객체 비교 510회 차이 0. 후보 rowid 대조 56회 누락 0. T01~T11 전부 PASS, 공개 qrels 객체 대조 A=C. 초기 실패 로그 및 수정 내역 보존. C 개발 성능의 A 새 연결/C 재사용 연결 수치는 공식 후보 비교에 사용할 수 없다. 같은 연결의 C 가속/강제 폴백 진단은 별도 로컬 기록이다. 운영 회귀, 보류, 1/5/10배 공식 성능 NOT_TESTED.

첫 CLI 실행은 1,000초 상한 종료(143)로 보고서 마무리가 남았다. 후속 C 실행은 src/tests를 읽기 전용으로 두고 output의 보고서와 체크섬만 작성했고 종료 0이었다. 두 번째 실행에서 모델이 요청한 쓰기 작업은 output 4개 파일에 한정됐다. 근거 `C_EXECUTION_EVIDENCE.json`, `C_EXECUTION_FINALIZE_EVIDENCE.json`.
