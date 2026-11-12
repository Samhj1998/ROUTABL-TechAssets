# DW-01. 두 AI 분업 개발·검증 방식 v1.0 (2026-11-11)

- 등록: 2026-11-11 KST, Claude 세션 (사용자 요청 "이 방식 기술자산에 업데이트해줘")
- 첫 적용: 라우터블 분석앱 `verifySharedHash` 추가 → 커밋 `b960472` (origin/main 반영)
- 위상: 개발 작업 방식 원칙. VI-01(버전 독립)·TI-01(3단계 원본 보호)의 하위에서 적용

## 1. 왜 만들었나

- 예전 방식: 클라우드에서 수정 → 압축 → Mac 전송 → 풀기 → 커밋 → 빌드 오류 캡처 → 다시 수정. 왕복마다 시간과 크레딧 소모.
- 원인: Claude 쪽 원격 셸은 macOS 빌드와 GitHub 접속이 안 되고(403), ChatGPT 쪽은 Mac에서 직접 실행할 수 있음.
- 해법: 각 AI가 잘하는 단계만 맡고, 검증을 통과한 것만 커밋한다.

## 2. 역할 분담

| 주체 | 맡는 일 | 못 하는 일 / 금지 |
|---|---|---|
| Claude (원격 연결 셸, 연결 폴더) | 코드 읽기·분석·수정, 원인 진단, 실행 프롬프트 작성, 결과 판정, 기록 | macOS Gradle 빌드, GitHub 푸시(403) |
| ChatGPT + Desktop Commander (Mac 직접 실행) | Gradle 빌드·테스트, 부정 시험, 커밋·푸시 | 삭제, 운영 Firebase 쓰기 (사전 승인 없이는 금지) |
| 사용자 | 프롬프트 전달, 결과 붙여넣기, 승인, 실기기 확인 | — |

## 3. 표준 순서

1. Claude가 연결 폴더에서 코드를 수정하고, 같은 규칙을 가능한 범위에서 미리 시험한다 (예: 해시 비교를 파이썬으로 모의 시험).
2. Claude가 ChatGPT용 실행 프롬프트를 쓴다 (아래 4절 규칙).
3. 사용자가 ChatGPT에 붙여넣고, ChatGPT가 Desktop Commander로 Mac에서 실행한다.
4. 사용자가 결과 요약을 Claude에 붙여넣는다.
5. 실패면 Claude가 원인을 고치고 2로 돌아간다. 성공이면 Claude가 저장소 상태(git log, status, origin/main 일치)를 직접 확인한다.
6. 기록: 저장소 docs/ 인계문 + 기술자산 등록.

## 4. 실행 프롬프트 규칙

- 출력은 요약만, 오류는 마지막 30줄만 (대량 출력으로 연결이 멈추는 것 방지)
- 매번 끝에 금지문: "삭제나 운영 Firebase 쓰기는 하지 마."
- 커밋·푸시는 조건부: 빌드 성공 **그리고** 부정 시험 통과일 때만
- 부정 시험: 일부러 규칙을 어겨 검사가 실제로 막는지 확인 → 원상복구 → `git status` 깨끗한지 확인
- 무거운 작업(대용량 해시, 복사)은 한 번에 하나만

## 5. 커밋 전 검증 게이트 (전부 통과해야 커밋)

1. 빌드 검사 통과 (verifySharedHash, verifyReadOnlyFirestore 등)
2. 단위 테스트 통과
3. 디버그 빌드 성공
4. 부정 시험에서 실패가 정상 감지됨
5. 작업 트리 원상복구 확인

## 6. 알려진 함정 (재발 방지 목록)

| 증상 | 원인 | 해결 |
|---|---|---|
| `Unresolved reference 'security'` (build.gradle.kts) | Gradle 스크립트 안에서 `java`는 java { } 설정 블록으로 해석됨 | 파일 맨 위에 `import java.security.MessageDigest` |
| 원격 셸에서 git commit 후 `.lock` 남음 | 연결 폴더는 기본 삭제 금지 | 해당 폴더 삭제 권한을 받은 뒤 커밋, 또는 Mac에서 커밋 |
| 연결 폴더에서 sqlite 생성 시 disk I/O error | 마운트 폴더의 파일 잠금 | 로컬 작업 폴더에서 만든 뒤 복사 (v0.14 사고) |
| 원격 셸 `git push` 403 | Mac 쪽 원격 셸 네트워크 제한 | 푸시는 Mac 직접 실행(ChatGPT·Android Studio) |
| Claude 앱 연결 멈춤 | 원격 통로에 대용량 출력·해시·NAS 연결이 동시에 몰림 | 4절 규칙. 앱이 응답 불능이면 Mac에서 강제 종료 후 재실행 |
| 작업 폴더 이름과 실제 버전 불일치 | `DISPATCH-One-Android-Latest`의 작업 파일은 1.0.18(10/13), origin/main만 최신 | 조사 전에 `git log -1`과 versionName 확인, `git show origin/main:`으로 읽기 |
| 다른 AI의 운영 DB 쓰기 | Desktop Commander는 폴더 제한 없이 홈 전체·운영 Firebase 접근 가능 | 운영 쓰기는 사전 승인 후 실행 |

## 7. 재사용 자산

- `verifySharedHash`: 라우터블 분석앱 `app/build.gradle.kts` (커밋 b960472). shared/ 해시가 `SHARED_SOURCE.md`와 다르거나, 파일이 빠지거나 늘면 preBuild에서 실패. 숨김 파일(.DS_Store) 제외.
  - 적용 후보: 시니어앱 `ROUTABL-Senior-Driver`, 고객등록앱(예정). 기사앱은 shared 원본이라 해당 없음.
- 2026-11-11 기준 shared/ 일치: 기사앱 b9c40c2 = 시니어앱 = 분석앱 (17개 파일).

## 8. 첫 적용 기록 (2026-11-11)

| 단계 | 결과 |
|---|---|
| Claude 수정 + 파이썬 모의 시험 | 17건 통과, 변경·추가 감지 |
| 1차 Mac 실행 | 스크립트 컴파일 실패 (`java.security`) → 커밋 안 함 |
| Claude 수정 (import) | — |
| 2차 Mac 실행 | 해시·읽기 전용 검사, 단위 테스트, 디버그 빌드 성공. 부정 시험 감지 성공. 원상복구 |
| 커밋·푸시 | b6d8914, ab621fe, b960472 → origin/main |
| 금지 사항 | 삭제·운영 Firebase 쓰기 없음 |
