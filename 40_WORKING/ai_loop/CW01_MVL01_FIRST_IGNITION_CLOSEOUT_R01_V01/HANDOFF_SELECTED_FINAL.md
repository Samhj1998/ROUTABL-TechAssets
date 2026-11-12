# Digitopia MVL-01 독립 AI 개발 인계

목표는 기존 v1.5 검색을 재사용해 최신 대장 연결과 검증 가능한 결과 환류를 완성하는 것이다.
고정 참조와 명시적으로 선택한 격리 후보의 로컬 파일을 인계 생성 시점에 검증했다.

## 확인된 동작과 재사용

- 운영 v1.5는 출처 연결에 v0.6을 고정 참조한다. v0.6과 v0.27의 출처 연결 두 건은 동일하다.
- v1.5 검색 SQL·별칭·순위·SHA 기준 중복 묶음을 재사용한다. v1.4에서 DB 검사 기능을 재사용한다.
- CW-01의 자산 ID·경로·SHA-256 인계 방식과 AF-01의 접근 우선 방향을 적용한다.
- v0.27의 번호·해시·스키마·ID를 확인한다. 검색 색인 기대값과 원본 직접 해시를 구별한다.

## 인계에 포함된 기술자산

| ID | 출처 경로 | 판본 | 기대 SHA-256 | 실측 SHA-256 | 검증 상태 | 등록 구분 |
| --- | --- | --- | --- | --- | --- | --- |
| ASSET-SEARCH-V15-SERVICE | /Users/yongho/Library/Application Support/ROUTABL-AssetSearch/routabl_search_v1_5_service.py | 1.5 | 55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d | 55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d | LOCAL_HASH_MATCH | OFFICIAL_ROW |
| MVL01-REGISTRY | /Users/yongho/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.27.json | 0.27 | afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244 | afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244 | LOCAL_HASH_MATCH | REGISTRY_DOCUMENT |
| AF-01 | /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_ACCESS_FIRST_PRINCIPLE_AF01_V01/DIGITOPIA_ACCESS_FIRST_PRINCIPLE_AF01_v1.0_20261108.md | 1.0 | 13eadac676aed2e97c0486edbed67c9db85a1d693545de80db209830614805d5 | 13eadac676aed2e97c0486edbed67c9db85a1d693545de80db209830614805d5 | LOCAL_HASH_MATCH | PINNED_REFERENCE |
| CW-01 | /Users/yongho/ROUTABL-TechAssets/00_GUIDE/DIGITOPIA_CHAT_WORK_PROTOCOL_v1.0.md | 1.0 | 7b48c1deb08ab1c8904541f7c9acedbf2406e51f510fbccf0d7ae17609d585d1 | 7b48c1deb08ab1c8904541f7c9acedbf2406e51f510fbccf0d7ae17609d585d1 | LOCAL_HASH_MATCH | PINNED_REFERENCE |
| MVL01-CW-POC | /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_HANDOFF_POC_V01/VERIFICATION_RETEST.md | 미명시 | e1fb4a7504d08cd234621c020439e57578145e5277d66d1a842f2a46bc759bbf | e1fb4a7504d08cd234621c020439e57578145e5277d66d1a842f2a46bc759bbf | LOCAL_HASH_MATCH | PINNED_REFERENCE |
| MVL01-CW-COLD | /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_HANDOFF_COLDSTART_V01/HANDOFF_MANUAL.md | 미명시 | bf8a093caf412b45f8400efda3b9a0bb6fea26b7af0b0378b3f648ea60eed688 | bf8a093caf412b45f8400efda3b9a0bb6fea26b7af0b0378b3f648ea60eed688 | LOCAL_HASH_MATCH | PINNED_REFERENCE |
| MVL01-CW-FEEDBACK | /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_STEP5_FEEDBACK_V01/HANDOFF_OUTPUT_CONTRACT_v0.1.md | 0.1 | c5735b796213cb93f718167ed5a2b4006b6a1816991a6d7eb71520053666e455 | c5735b796213cb93f718167ed5a2b4006b6a1816991a6d7eb71520053666e455 | LOCAL_HASH_MATCH | PINNED_REFERENCE |
| MVL01-FEEDBACK | /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/FEEDBACK_CANDIDATE.md | 0.1 | 04402d26ebc08985acd63a49bba77064deb315c02b994197165adef8d8d861b3 | 04402d26ebc08985acd63a49bba77064deb315c02b994197165adef8d8d861b3 | LOCAL_HASH_MATCH | ISOLATED_CANDIDATE |
| MVL-USER-R01-SELECTED-HANDOFF | /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/incoming/R01_SELECTED_HANDOFF_FEEDBACK.md | 1.0 | d27779d4c17db58fedcb8e16ab9b52eea637b3e80cd53baddf41206eccda5242 | d27779d4c17db58fedcb8e16ab9b52eea637b3e80cd53baddf41206eccda5242 | LOCAL_HASH_MATCH | ISOLATED_CANDIDATE |

## 수신자가 검토할 과제

독립 승인에 기재된 격리 코드와 증거만 사용해 대장 선택·출처 검증·환류 재검색을 검토한다.
잘못된 원본 경로, 해시 불일치, 민감 자료 포함, 회귀 가능성을 확인하고 재현 가능한 검토 결과 또는 개선안을 반환한다.
기대 산출물은 코드 차이 검토, 시험 명령·결과, 재현 조건, 성공·실패·미검증을 구분한 보고다.
등록되지 않은 후보와 공식 대장 행을 구별한다. 독립 수신자의 직접 파일 검증은 실제 수행 근거가 있는 경우에만 기록한다.

## 실행 경계

제출과 접근은 별도 승인 범위에서만 수행한다. 기본 인계는 정적 기술 메타데이터로 구성한다.
운영 검색·DB·공식 대장·원본·백업·라우터블 운영 서비스는 변경하지 않는다.
외부 게시, 원본 본문 전송, 고객정보·비밀번호·토큰·키 전달은 금지한다.

## 결과 반환 필드

수신 환경, 사용 자료 ID·경로·기대/실측 SHA-256, 확인 방식, 실제 검토·변경 내용, 재현 명령, 결과, 미검증, 권한 준수, 다음 판단을 기록한다.
