# Step 4-C 입력 및 동결 검증

MacStudioui-MacStudio.local · c377300b-a710-43a6-8169-f17e87175403. 운영 A 소스 SHA 55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d, DB SHA c5a800f36aaaeddd1b5aad086403df115fa8f99fb8f616271421e89dff71cba4. 운영 DB의 측정 입력은 `private/operating.sqlite`에 SQLite Backup API로 만든 로컬 사본이다. 사본 quick_check 통과, SHA c7fc620620e87f885b506f72c14fcd68644a381dae58d8c1acf5b976e1359f22. 백업 사본의 물리 바이트는 운영 원본과 별도로 고정했다.

Step 4-B 증거 체크섬 SHA b2f51c92eb8d163e2dcce122d89c69dbcb32a8fd33d2576e402cc70a921da522의 18건, B 자체 체크섬 10건, C 자체 체크섬 12건을 사전 검증했다. B/C 소스는 원본과 바이트가 같은 평가용 복제본을 사용했다. B의 Step 4-B 작업 DB 21건은 원래 위치를 보존했다. 평가용 쓰기 DB는 이번 폴더 `tests/` 아래에 생성했다. C 동결 시험 러너는 실행하지 않았다.

`private/EVALUATION_COHORT_PRIVATE.json` SHA a5aa8fac99eaddf410a89fa7a7b0a05bdd9c9e298473557b1dd01efe9ec43efc, `private/EVALUATION_BOUNDARY_AUXILIARY.json` SHA ddf5a17d75f9693ec2a998f477a0e4e496929a971c668afb7009fd79aef1da52. 측정 직전 별도 고정한 정확한 보조 DB·주입·반복 계획 `private/measurement_plan.json` SHA b9ea9aea08c685aa274bb42b2b217b3929bdd5ab8fa0dec847d092d40514436f.

후보 실행과 운영 검색어 및 반환 객체 비교는 지정 Mac 내부에서만 수행했다. 공개 보고서에는 운영 검색어·경로·본문이나 평가자 전용 보류 문자열을 포함하지 않았다. 최종 재검산은 `private/postverify.json`.
