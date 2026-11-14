# 기술자산 대청소 진단 (2026-11-14, 읽기 전용 — 삭제 없음)

기준: 사용자 전제 ① 기술자산은 공개 자료 ② 가치는 다음 프로젝트에서의 활용도. 삭제·이동은 모두 **승인 후**.

## 0. 한눈에
| 구분 | 현재 | 정리 후(제안) |
|---|---|---|
| 디스크 전체(.git 제외) | 약 8.3GB / 751개 | 약 3.0GB (−5.3GB) |
| git 추적 파일 | 576개 | 약 150개 (과정 기록 → 요약 1장씩 + git 이력 보관) |

## 1. 가장 중요한 발견: 기술자산의 '알맹이'는 이 폴더에 별로 없다
- 등록부 자산 210개 중 **94개가 이 폴더 밖**(주로 `~/StudioProjects` 앱 코드: 초성검색·리스너·캐시·정산 등).
- 이 폴더의 git 추적 576개 중 약 400개는 **기술자산을 관리·백업·검색하는 과정 자체의 기록**(백업 게이트 B3~B6, AI 인계 시험 MVL·CW01, 검색 벤치마크 121_W).
- 즉 '다음 프로젝트에 쓰는 지식'보다 '자산 관리 시스템을 만드는 과정'이 대부분 → 사용자 판단(자산 자체 완성도에 치우침)과 일치.

## 2. 디스크 정리 후보 (git 밖 파일)
| # | 대상 | 크기 | 근거 | 조건 |
|---|---|---|---|---|
| D1 | `20_ORIGINALS/ChatGPT-Account-Exports/.../NAS_INDEPENDENT_RECOVERY_*.sparseimage` 2개 | 3.2GB | 옆 파일과 **바이트 동일**(SHA 일치) — 복원 시험 결과물 | 없음 |
| D2 | 같은 폴더 `30_ENCRYPTED_LOCAL/` 암호화 v1 | 1.6GB | v2(비밀번호 줄바꿈 수정판)가 대체 | v2 열림 1회 확인 |
| D3 | 같은 폴더 암호화 v2 자체 | 1.6GB | 원본 zip(1.5GB)과 같은 내용의 암호화본. 비공개 층은 NAS 보관으로 충분 | NAS에 원본 zip 사본 확인 후 (선택) |
| D4 | `40_WORKING/ai_loop/*/assets_v1_5.sqlite` 3개 + 벤치마크 `private/*.sqlite` | 약 370MB | 같은 DB 사본(SHA 동일 2~4중), 끝난 시험 | 없음 |
| D5 | `40_WORKING/backup/NAS_INDEPENDENT_RESTORE_20261103…` | 59MB | 11-03 복원 시험 잔여 이미지 | 없음 |
| D6 | `40_WORKING/backup/RESTORE_TEST_20261103_v1` | 4.7MB | 백서 PDF 사본(원본과 SHA 동일) | 없음 |
| D7 | `30_REGISTRY/_archive_versions` | 7.4MB | 등록부·조회DB 옛 판(git 이름표에 전부 있음) | **백업 v3 설치 후**(옛 백업이 v0.32 사본을 읽음) |
| D8 | `70_EXPORTS/*.zip` 5개(옛 백업 관리자 앱) | 0.3MB | 백업 v3로 대체 | 백업 v3 설치 후 |
| D9 | `30_REGISTRY/_to_delete`, `_history_archive/private_files` | 0.3MB | 이미 삭제 대기 / 원위치에 같은 파일 존재 | 없음 |
| 유지 | `80_RUNTIME/ASSET_SEARCH_V1_8/index_v1_8.sqlite`(206MB) | — | 현재 검색 서비스가 사용 | — |
| 유지 | ChatGPT 원본 zip(1.5GB), 10_CHAT_120 | — | 유일 원본 | — |

## 3. git 추적 정리 후보 (과정 기록 → 요약 + 이력 보관)
방법: 정리 직전 이름표 `pre-cleanup-20261114` → 폴더를 현재 트리에서 제거 → 폴더마다 **교훈 요약 1장**(무엇을 시험했고, 결론, 다음에 재사용할 원리)만 남김. 원본은 이름표로 언제든 복원.

| 묶음 | 파일 수 | 성격 | 제안 |
|---|---|---|---|
| `40_WORKING/backup/CW01_BACKUP_GATE_B3~B6*` (6개) | 106 | 폐기 예정인 백업 체계의 단계별 게이트 기록 | 요약 1장 + 이력 |
| `40_WORKING/backup/TEST_LAUNCHD_*`, `VERIFY_*`, `BACKUP_HEADLESS`, `HEADLESS_NATIVE`, `SELECTIVE_BACKUP_V2_2_DRAFT` | 21 | 옛 백업 실험·앱 소스 | 백업 v3 3일 성공 후 요약 + 이력 |
| `40_WORKING/ai_loop/CW01_*` (11개) | 134 | AI 인계 루프 시험(MVL·콜드스타트 등) | 요약 1장(인계 원칙) + 이력 |
| `40_WORKING/search/121_W_*` (10개) | 133 | 검색 벤치마크·Claude 설치 시험 | 결론(측정치·채택 방식) 1장 + 이력 |
| `customer/.../_superseded`, `*_v0.1/0.2` 형제 파일 | 8 | 같은 문서 옛 판 | 최신만 남기고 이력 |
| `70_EXPORTS/AI_ASSET_DISCOVERY_v0.1~0.3` | 3 | 같은 안내문 옛 판 | 최신 1개(이후 V1-6 안내로 통합) |

남는 것(약 150개): `00_GUIDE`(원칙·안내), `30_REGISTRY`, `60_AUDIT`(판단 근거 기록), `40_WORKING/customer`(파서·시험), `search/ASSET_SEARCH`, `121_D/E/F`(설계 원칙), 각 묶음 요약 문서.

## 4. 정리 순서 제안
1. 즉시 가능(조건 없음): D1·D4·D5·D6·D9 → 약 3.6GB
2. 백업 v3 설치·3일 성공 후: D7·D8 + 백업 관련 git 정리
3. 사용자 확인 후: D2·D3(ChatGPT 내보내기 암호화본), ai_loop·121_W 요약 정리
