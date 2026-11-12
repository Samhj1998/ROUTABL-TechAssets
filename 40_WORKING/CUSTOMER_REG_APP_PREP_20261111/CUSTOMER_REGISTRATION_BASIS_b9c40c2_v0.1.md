# 고객등록앱 설계 근거 — 기사앱 b9c40c2 기준 v0.1 (2026-11-11)

- 조사: Claude, 읽기 전용. 대상 `~/StudioProjects/DISPATCH-One-Android` (HEAD = origin/main = b9c40c2, 1.0.68)
- 오전 ChatGPT 조사 중 `-Latest`(1.0.18) 작업 파일을 읽은 부분은 이 문서로 대체
- `codex/customer-quick-registration-20261019` 브랜치는 main에 이미 병합됨

## 1. 핵심 결론
**등록→검수→확정 흐름은 기사앱과 Firestore 규칙에 이미 완성되어 있다.** 고객등록앱은 새 데이터 구조나 새 규칙 없이, 기존 `customerSubmissions` 요청과 관리자 검수를 쓰는 얇은 앱으로 만들 수 있다.

## 2. 데이터 구조
| 컬렉션 | 용도 | 쓰기 권한 |
|---|---|---|
| `customers/{고객명}` | 공용 주소록. 문서 ID = 고객명 | 관리자만 (승인 기사는 읽기) |
| `customerSubmissions/{요청ID}` | 기사의 신규·수정 요청 (pending→approved/rejected) | 승인 기사: 본인 요청 생성·보완 / 관리자: 검수 |
| `customerDirectoryChanges/{고객ID}` | 증분 동기화 기록 (삭제 기록 보존) | 서버 함수만 (`dispatchSyncCustomerDirectory`) |

고객 필드 10개 (`CustomerFields.names`): name, dong, address, roadAddress, phone1, phone2, memo, lat, lng, searchAliases

## 3. 검증 규칙 (앱 `CustomerStore.validate` = 서버 `customerPayload`)
- 고객명·동명 필수, 고객명 100자·`/` 금지, 주소 500자, 메모 2,000자, 별칭 2,000자
- 전화 24자, 숫자와 `+*#(), -`만
- 위도·경도 필수 유효값 (`CustomerCoordinates.valid`)
- 요청 필드는 정해진 목록만 허용, `ownerUid`=본인, 수정 요청은 `baseData`(신청 당시 원본) 필수

## 4. 재사용할 코드 (기사앱)
| 파일 | 역할 | 재사용 방식 |
|---|---|---|
| CustomerStore.kt | validate / submit(기사 요청) / review(관리자 검수) / saveShared | **submit·validate 핵심**. review는 관리자 기능 넣을 때만 |
| CustomerSearch.kt (CustomerFields) | 필드 정규화 | 그대로 |
| CustomerAddressPolicy.kt | 지번 기본, 도로명은 메모에 "도로명주소:"로 보존, 입력주소 보존 | 그대로 (주소 표기 통일의 핵심) |
| CustomerGeocoder / CustomerCoordinates / CustomerAddressLookup | 주소→좌표 | 그대로 |
| CustomerEditActivity.kt (493줄) | 입력 화면 | 화면은 새로 쓰되 흐름 참고 |
| CustomerReviewActivity.kt | 관리자 검수 화면 | 검수를 등록앱에 넣을지 결정 필요 |
| CustomerDirectory.kt (484줄) | 주소록 캐시·증분 동기화 | 중복 확인용 조회에 필요 |
| shared/KoreanSearch | 초성 검색 | shared 복사 + verifySharedHash |

## 5. 등록앱이 지켜야 할 것
- 공용 주소록(`customers`)에 직접 쓰지 않는다 → 반드시 요청(`customerSubmissions`)으로. 확정은 관리자 검수
- 고객명이 문서 ID → 같은 이름 중복은 신규 요청 단계에서 막힘. "기존 고객 연결" 흐름 필요
- 배차 당시 스냅샷(DATA-01)과 주소록을 섞지 않는다
- 운영 DB 쓰기 시험은 사전 승인 (DW-01)

## 6. 범위 결정이 필요한 질문
1. 누가 쓰나: 기사들만 / 사용자 본인(검수)도
2. 검수(승인·반려)를 등록앱에 넣나, 기사앱 관리자 화면을 계속 쓰나
3. 기존 고객 수정 요청도 받나, 신규 등록만 하나
4. 사진·위치 안내(찾아가는 길) 입력을 메모 외 별도로 받나
5. 저장소 위치: 기사앱 저장소 안 모듈(고객앱처럼) / 별도 저장소(분석앱처럼)
