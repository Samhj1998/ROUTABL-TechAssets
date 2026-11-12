# 120-1. ChatGPT 아카이브 v0.4 — Markdown 서식 복원 및 라우터블 19+2 채팅 확인 기록

**기준:** 사용자 명시 요청 2026-11-06. Mac Studio에서 진행.  
**원본:** ChatGPT 공식 2026-11-05 내보내기 ZIP, 327개 채팅.  
**새 GUI:** `/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05/13_GUI_MARKDOWN_V04/index.html`

## 1. 사용자 요청 해석

1. 공식 내보내기에서 평문으로 노출되던 Markdown 표 (`| 점검 항목 | 확인 결과 |`), `**bold**`, 제목, 목록, 코드 블록, 인용문을 사람이 직접 읽기 쉬운 HTML 서식으로 복원.
2. 사용자가 ChatGPT에서 보관 해제하고 라우터블 프로젝트로 옮겼다고 명시한 **기존 라우터블 프로젝트 ID 19건과 추가 2건**을 독립 로컬 아카이브의 공식 대조·관리 기록에 반영. 해당 ChatGPT 계정 변경을 AI가 실행하거나 현재 계정에서 독립 확인했다고 주장하지 않음.
3. 원본 ZIP, 2026-11-05 당시 보관 상태, 과거 v0.1/v0.2/v0.3 GUI, SSD/NAS AES-256 백업을 훼손하지 않음.

## 2. 공식 원본과 현재 사용자가 보고한 상태를 분리

- `g-p-6a92532988c881918be08fc0ad4dbaed` 프로젝트에 실제 소속된 **119건**: 원본 ID 유지.
- 이 중 2026-11-05 `is_archived=true`인 **19건**: 2026-11-06 사용자 복원·보관 해제 확인 기록 추가, 당시 필드는 유지.
- 2026-11-05 원본 `conversation_template_id=null`인 보관 채팅 **2건**:
  - `고객 주소록 등록`: `6ac5b1ff-1e44-83ee-9356-8640bf3141d0`
  - `Firebase 요금 변경 알림`: `6ad49d36-3a8c-83ee-96c1-aadc0c7b4e86`
- 추가 2건은 사용자가 2026-11-06 실제 ChatGPT 라우터블 프로젝트로 이동했다고 명시했으므로 `effective_project_id` **GUI 표시에만** 라우터블 ID 연결. 원본 `project_id:null`은 보존하고 `USER_CONFIRMED_MOVED_PROJECT_SOURCE_ID_NULL` 출처 정보로 기록.
- **GUI 실제 표시:** 라우터블 121건(원본 ID 119건+사용자 확인 2건), 원본 프로젝트 ID 없는 미분류 161건(원본은 163건), 21건 사용자 복원 확인 필터 제공. 전체 채팅 327건은 변함없음.
- GUI의 `11/5 당시 보관` 필터는 **스냅샷 원본 기준**, `11/06 사용자 복원 확인` 필터는 후속 이용자 진술 기준이다. 혼동을 막도록 시점이 표시됨.

## 3. Markdown 표시 엔진

- Mac Studio에 설치된 local `markdown-it` 라이브러리를 **빌드 시에만** 사용해 정적 HTML 생성; Safari 열람 시 추가 런타임·CLI·네트워크·서버가 필요하지 않음.
- 안전 설정: `html:false`, `linkify:false`, `breaks:true`, `typographer:false`. 미리보기에서 raw HTML·script 실행 불가, Markdown의 원격 이미지 자동 로딩을 텍스트 참조로 제한. 첨부 이미지 원본 링크는 기존의 로컬 assets 연결 유지.
- UI 구성: Markdown 표 스크롤·헤더 색상·행 구분, 코드블록 별도 어두운 배경, 인라인 코드, 단계별 제목, 목록, 인용문, 굵은 글씨, 취소선, 링크, 구분선. 모바일·좁은 창에서도 표 좌우 스크롤.
- **변환 결과 (327개 HTML 페이지):** Markdown 본문 12,920개, 표 1,496개, 제목 4,856개, 코드 블록 2,815개, 굵은 글씨 35,912개, 인용문 721개, 목록 4,159개.
- 이전 GUI v0.3의 327개 대화 원문 HTML 페이지는 불변; 공식 JSON/ZIP도 불변.
- 일부 ChatGPT 전용 DIL·리치 UI 표시는 원문 텍스트로 남을 수 있음. 이것은 전체 ChatGPT UI 재현이 아니라 Markdown 서식 복원이며, 미지원 요소를 임의 실행하지 않음.

## 4. 검증 기록

- `/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05/20_AUDIT/v04_restoration_overlay_preflight_20261106.json`
- `/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05/20_AUDIT/v04_markdown_render_receipt_20261106.json`
- `/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05/20_AUDIT/v04_browser_acceptance_20261106.json`
- Chrome 실제 오프라인 GUI 사용성 자동시험 **15/15 PASS**: 전체 327건, 실제 라우터블 표시 121건, 21건 사용자 복원 필터, 추가 2건의 원본 ID 없음과 사용자 이동 확인, 원본 보관 상태, Markdown 표 HTML 전환, 테이블 CSS 적용, 대화 상세 복원 기록.
- 327건 전체 채팅 HTML 및 기존 첨부 링크 유지. 라이브러리 폴더·기존 백업 루틴·Firestore·앱 프로젝트 무변경.
- Safari 사용자 직접 화면 승인 단계는 **PENDING**: 실제 Mac에서 표를 읽어보고 표시 품질 확인 권장.

## 5. 저장 및 복원 정책

- 사용자 복원 이력 상세 근거: `13_GUI_MARKDOWN_V04/restoration-ledger.json` (21개 `conversation_id`와 11/5 원본 상태, 11/6 사용자 발언)
- 원본 v0.3 `project-id-ledger.json`과 11/5 공식 `conversations-*.json`은 수정하지 않음.
- 복원 이력은 Mac 로컬의 버전관리 대상 문서로 등록. 2026-11-05 이후 플랫폼 상태를 실시간 동기화하거나 ChatGPT 계정에서 실제 보관 해제·프로젝트 이동을 이 작업에서 실행하지 않음.
- 바탕화면 기본 GUI를 v0.4로 갱신; 이전 v0.3 바로가기를 별도 보존. 기존 v0.1/v0.2 바로가기도 유지.
- 백업본과 원문은 분리. 평문 아카이브를 NAS/SSD로 무심코 복제하지 않음.

**판정:** v0.4 GUI Markdown 변환·사용자 복원 확인 이력 반영·Chrome 오프라인 자동검증 PASS, 사용자 Safari 실기기 화면 검증 PENDING.
