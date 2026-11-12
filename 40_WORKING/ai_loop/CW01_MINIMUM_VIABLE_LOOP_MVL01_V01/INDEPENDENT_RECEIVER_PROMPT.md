# MVL-01 독립 수신용 프롬프트

120-2 Chat과 120-2-W의 기존 대화에 기대지 말고, 별도로 승인된 자료와 직접 수행한 검토를 근거로 작업한다. 사용자가 독립 세션 실행과 허용 자료를 별도로 승인한 뒤 적용한다. 이전 세션의 판정을 자신의 직접 검증으로 옮기지 않는다.

목표는 기존 기술자산을 활용해 검색 v1.5의 최신 대장 연동과 환류 재검색 개선을 실제 개발 과제에서 검토하고 활용하는 것이다. v0.6과 v0.27의 기존 출처 연결 두 건은 동일했다. 격리판은 검색 기능을 재사용하면서 원본 경로·판본·기대값·실측값을 구분한다.

- `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/HANDOFF_FINAL.md` SHA-256 `470db7b07e2148352c42aad81e8610943e97aae4a940c0d9c6aa864be5845acb`
- `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/FEEDBACK_CANDIDATE.md` SHA-256 `04402d26ebc08985acd63a49bba77064deb315c02b994197165adef8d8d861b3`
- `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/mvl.py` SHA-256 `6aa94e2c46aea8b70313952dba7440c71696542d2fc64413b5cb7cb7f9b3b1b3`
- `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/mvl_provenance.py` SHA-256 `58cfd63bde15618a5d3e870a3080e1d3ce41e62301fa257865fdcf9cff294e6c`
- `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/routabl_search_v1_5_service.py` SHA-256 `f391044addc200f7c2cd70cb68163e913751c619b5a9b8ff42afc824e08885fc`
- `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/test_mvl.py` SHA-256 `09541d61260f5ec8f4272b3660ef866f3f27e01f85434695c30bf314d8bed0f6`
- `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/CODE_DIFF.patch` SHA-256 `4d95b340ec52c7d7e00f0c73b89a6803b330f9daf92cb551d9049cfd0c28346e`
- `/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MINIMUM_VIABLE_LOOP_MVL01_V01/TEST_RESULTS_FINAL.json` SHA-256 `ad66ccbd3ee5eb5b6daa588de3b5c0d3c120fb18b4a72285f9c1f2960446ca92`

최소 입력은 HANDOFF_FINAL.md다. 추가 경로는 사용자가 해당 파일 또는 범위를 명시적으로 승인했을 때만 제공하거나 접근한다. 운영 DB·공식 대장 전문·고객정보·비밀번호·토큰·키는 제출하지 않는다. Mac 원격 접근이 승인되지 않았으면 제출된 자료만 읽는다. 수정이나 시험이 필요하면 사용자가 별도로 지정한 독립 사본에서만 수행한다. 위 격리판이나 운영 자료를 변경하지 않는다.

1. 초기 응답에서 목적·재사용 기술·금지 범위·입력 ID와 기대 해시를 복원하고, 직접 검증 여부를 구분한다.
2. 승인된 코드·증거로 최신 판본 선택, 원본 바이트 검증, 기존 검색 보존과 환류 재검색을 실제로 활용한다. 대표 사용 사례 한 건을 수행해 재현 가능한 검토 결과 또는 개선 코드·시험을 반환한다. 자료가 부족하면 수행하지 못한 단계와 필요한 최소 자료를 기록한다.
3. 최종 응답에 수신 환경, 사용한 파일과 기대/실측 SHA-256, 실제 조치와 명령·결과, 개선 산출물, 회귀·실패 사례, 미검증·경계 준수 여부를 기록한다. 출처 재현과 직접 검증은 별도 판정한다.
4. 결과를 사용자에게 반환한다. 사용자가 120-2-W에 수동 제출하면 독립 결과와 기존 로컬 결과를 분리해 평가한다.

백업·복원·운영 배포·Step 5-C 게시·공개 전송은 이 실험 범위에서 제외한다.
