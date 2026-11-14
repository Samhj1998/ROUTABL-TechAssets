# 백업 v3 설치 안내·격리 시험 기록 (2026-11-14)

## 구성 (3개 파일)
| 파일 | 역할 |
|---|---|
| `backup_v3.sh` | 백업 스크립트(약 40줄). `daily`: push(GitHub·NAS) + fsck + git 밖 파일 rsync. `push-only`: push만 |
| `post-commit` | 커밋 직후 `push-only`를 백그라운드로 실행(git hook) |
| `com.routabl.backup.v3.plist` | 매일 03:30 `daily` 실행(launchd). 기존 v0.4.2(04:30)와 시각이 겹치지 않음 |

기록: `80_RUNTIME/backup_v3/runs.log` (실행마다 JSON 1줄: 시각·결과·단계별 ok/FAIL·실패 사유). 실패·2일 이상 공백 시 macOS 알림.

## 격리 시험 (가짜 저장소·폴더, 실제 NAS·GitHub 미사용) — 8/8 PASS
| # | 상황 | 기대 | 결과 |
|---|---|---|---|
| T1 | 정상 | 두 원격 push·이름표·파일 복사, ok 기록 | PASS |
| T2 | 바로 재실행 | 문제없이 ok(반복 안전) | PASS |
| T3 | NAS 저장소 없음 | FAIL + 사유 기록 + 알림, GitHub 쪽은 계속 진행 | PASS |
| T4 | 파일 복사 대상 없음 | FAIL + rsync 오류 사유 기록 | PASS |
| T5 | 마지막 성공 3일 전 | "2일 넘게 지났습니다" 알림 | PASS |
| T6 | 커밋 직후 push-only | 두 원격 최신 커밋 일치 | PASS |
| T7 | `/Volumes/…` 미연결 | "NAS 볼륨이 연결돼 있지 않음" 사유로 FAIL(빈 폴더에 잘못 복사하지 않음) | PASS |
| T8 | 수정 후 정상 재확인 | ok | PASS |

미검증: 실제 Mac launchd 환경(아래 주의), 실제 NAS 볼륨, 실제 GitHub.

## 설치 (승인 후, 사용자 터미널, 약 2분)
```
cd ~/ROUTABL-TechAssets && cp 40_WORKING/backup/BACKUP_V3_REDESIGN/post-commit .git/hooks/post-commit && chmod +x .git/hooks/post-commit && mkdir -p /Volumes/Dev_Assets/TechAssets-files && bash 40_WORKING/backup/BACKUP_V3_REDESIGN/backup_v3.sh daily; tail -1 80_RUNTIME/backup_v3/runs.log
```
→ 첫 실행(약 7.7GB 복사라 수 분~수십 분). ok 확인 후 예약 등록:
```
cp ~/ROUTABL-TechAssets/40_WORKING/backup/BACKUP_V3_REDESIGN/com.routabl.backup.v3.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.routabl.backup.v3.plist && launchctl print gui/$(id -u)/com.routabl.backup.v3 | grep -E "state|path"
```

## 주의: macOS 네트워크 볼륨 권한
- 예약 실행(launchd)에서 `/Volumes/…`(NAS)에 접근하면 macOS가 권한을 막을 수 있음(11-03 기록에 "Operation not permitted" 사례). 터미널 실행은 되는데 예약 실행만 실패하면 이 경우.
- 해결 순서: ① 시스템 설정 → 개인정보 보호 및 보안 → **전체 디스크 접근**에 `/bin/bash` 추가 ② 그래도 안 되면 NAS로 **SSH 전송**(`BK_NAS_FILES=사용자@NAS주소:/volume1/…`, git 원격도 ssh 주소)으로 전환 — 마운트·권한 문제 자체가 사라짐(NAS SSH 켜기·키 등록 1회 필요).
- 실패해도 이제는 runs.log에 사유가 남고 알림이 뜨므로 바로 판단 가능.

## 전환 (3일 연속 ok 후, 승인)
v0.4.2 예약 해제·옛 관리자 앱 정리 → 대청소 진단 D7·D8 진행.
