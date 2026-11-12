# 고객등록앱·행정동 작업 기술자산 등록 기록 v1.0

- 작성: 2026-11-12 01:3x KST, Claude 세션 (사용자 요청 "기술자산에 추가해줘")
- 등록부: `30_REGISTRY/asset_manifest_v0.30.json` (v0.29 내용 무변경 + 13건 추가 + `customer_reg_app_v030`)
- 검색 색인: `30_REGISTRY/asset_120_lookup_v0.16.sqlite` (v0.15 복사 + 13행, 191행, integrity_check ok)
- 만든 스크립트: 같은 폴더 `build_registry_v030.py`

## 추가 자산 (registry_added_in v0.30, 등급 P3)

| asset_id | 파일 | 검증 상태 |
|---|---|---|
| CUSTOMER-REG-APP-01-CONSENSUS-V05 | 40_WORKING/CUSTOMER_REG_APP_PREP_20261111/CUSTOMER_REG_APP_CONSENSUS_v0.5.md | 합의안 ①~⑤ 모두 구현 |
| CUSTOMER-REG-APP-01-CAPTURE-PARSER | capture/CaptureParser.kt | 실기기, 사진 3000×4000, 메모 뒤 주소 줄 6b6531c |
| CUSTOMER-REG-APP-01-FIRST-REGISTRATION | register/FirstRegistration.kt | 실기기 중복(이름·전화), 행정동 동명 |
| CUSTOMER-REG-APP-01-SHARE-QUICK-PATH | share/ShareRegisterWorker.kt | 실기기 4단계 0f0c1a7 |
| CUSTOMER-REG-APP-01-REVIEW-QUEUE | register/ReviewQueue.kt | 실기기 5단계 6c73c97 |
| CUSTOMER-REG-APP-01-REVIEW-EDIT | review/ReviewEditActivity.kt | 실기기 d6cc4fd |
| CUSTOMER-REG-APP-01-HOME | HomeActivity.kt | 실기기 9bd6757·d6cc4fd |
| CUSTOMER-REG-APP-01-UI-COMMON | ui/Ui.kt | 실기기 ①③⑤, ④ 미확인 |
| CUSTOMER-REG-APP-01-HANDOFF-STAGE5 | docs/HANDOFF_STAGE5_20261111.md | 커밋 d6cc4fd |
| SERVER-ADDR-SEARCH-ADMIN-DONG | DISPATCH-One-Android server/control-routing/customer-address-policy.js | node 시험 68/68, routivel-prod 배포 00:12, ea537fe (승인 등급 C) |
| DRIVER-APP-ADDR-LOOKUP-ADMIN-DONG | DISPATCH-One-Android CustomerEditActivity.kt | 실기기 범어동→범어2동, 1.0.69 |
| SENIOR-APP-ADDR-LOOKUP-ADMIN-DONG | ROUTABL-Senior-Driver CustomerEditActivity.kt | 커밋·푸시, 빌드 미실행, 1.0.21 |
| CUSTOMER-DONG-NORMALIZE-TOOL | DISPATCH-One-Android tools/customer-dong/normalize_dongs.py | 단위 시험 5, plan 실행됨, apply 보류 |

모든 저장소 origin/main 반영(2026-11-12 01:27 사용자 푸시): 고객등록앱 d6cc4fd(새 비공개 저장소), 기사앱 ce85d7a, 시니어앱 766e658.
화면 구성안(Design 아티팩트 https://claude.ai/artifact/GrqffN8oRpUf2VZfg4JdE4)은 파일이 아니라 등록부 `customer_reg_app_v030.screen_design_artifact`에만 기록.

## 동명 일괄 정리 plan 결과 (2026-11-12 00:47, 쓰기 없음)
- 고객 1,979 / 바꿀 대상 1,833 (renamed 1,486 · numbered 347) / 이미 행정동 118 / 사람 확인 29 (지번 불일치 22 · 다른 동명 6 · 이름 '/' 1)
- **apply 전 확인 필요**: renamed(이름이 아예 바뀌는 경우)가 1,486건으로 예상보다 많음. 상위 표본:
  노원동3가→노원동 900, 중리동→상중이동 114, 이현동→상중이동 111, 갈산동→이곡2동 74, 월암동→월성2동 67, 대천동→월성2동 47, 갈산동→신당동 33, 장동→장기동 29, 노원동1가·2가→노원동 51 ('가' 붙은 법정동 합계 951)
  → 인성데이타·기사들이 실제로 쓰는 표기가 이 행정동(예: 상중이동)인지, 아니면 법정동(중리동)인지 사용자 확인 후 기준을 정할 것. 지금 기준대로 apply하면 동명이 기사에게 낯선 이름으로 바뀔 수 있음
- plan·백업 파일은 주소록 원본을 담고 있어 등록부에는 숫자만 기록 (파일 권한 0600)

## 해시
- 작업 전후 동일 (sha256sum -c): v0.29 등록부 78f13278…847d512f, v0.15 색인 3e409623…a0ec29
- v0.30 등록부 77565ce1…02296f3d, v0.16 색인 cac1be75…7498a2423

## 작업 방식
- 연결 폴더 위에서 sqlite를 직접 만들지 않음 (v0.14 사고). 작업 공간에서 만든 뒤 cp -n(덮어쓰기 없음)으로 복사, cmp로 같음 확인, 권한 0600

## 하지 않은 것
- 기존 v0.29·v0.15, 97-1 봉인본, NAS 백업, `~/Library` 자산 검색 서비스 DB, Firebase, 앱 코드: 변경 없음
- 자산 검색 앱 v1.6은 화면의 "검색 목록 새로 고침"을 눌러야 새 항목이 보임 (v1.6은 최신 등록부를 자동 선택)

## 추가 기록 (2026-11-12 01:36) — 카카오 행정동 사용 중단
- 사용자 결정: "상중이동은 안써", "왜 자꾸 카카오를 기준으로 하지?" → 동명 기준은 인성데이타 캡처와 주소록. 카카오 행정동은 쓰지 않음
- DISPATCH-One-Android 07fcfa0: 서버 adminDong 항상 '' (배포 대기), 동명 정리 도구 plan·apply 차단
- 따라서 v0.30에 등록한 아래 4건의 "행정동" 내용은 **폐기된 방식**. 등록부(v0.30)는 그대로 두고, 다음 등록부 버전에서 상태를 SUPERSEDED로 고칠 것
  - SERVER-ADDR-SEARCH-ADMIN-DONG, DRIVER-APP-ADDR-LOOKUP-ADMIN-DONG, SENIOR-APP-ADDR-LOOKUP-ADMIN-DONG, CUSTOMER-DONG-NORMALIZE-TOOL
- 위 "동명 일괄 정리 plan 결과"의 숫자(1,833 / 347)도 카카오 기준이라 의미 없음. 다시 할 때는 주소록 기준으로 설계
- 01:41 사용자 배포 완료 (routablCustomerAddressSearch, adminDong 항상 ''), 푸시: 기사앱 07fcfa0, 고객등록앱 4207313
- 00:12~01:41 사이 카카오 행정동이 잘못 들어간 고객: 없음 (사용자 확인 01:39). 케이비시테크 범어2동은 사용자가 원한 값
