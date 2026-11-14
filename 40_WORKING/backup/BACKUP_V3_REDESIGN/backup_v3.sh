#!/bin/bash
# 라우터블 기술자산 백업 v3 — 스크립트 1개. 설계: DESIGN.md (2026-11-14)
# 1층: git push (GitHub 공개 + NAS)  2층: git 밖 파일 rsync → NAS  3층: 결과 1줄 기록·실패 알림
# 원칙: 지우지 않음(rsync --delete 없음), 재시도해도 안전, 실패 이유는 항상 기록.
set -u
SRC="${BK_SRC:-$HOME/ROUTABL-TechAssets}"
NAS_FILES="${BK_NAS_FILES:-/Volumes/Dev_Assets/TechAssets-files}"   # 또는 ssh 대상: user@nas:/volume1/...
LOG_DIR="${BK_LOG_DIR:-$SRC/80_RUNTIME/backup_v3}"
STALE_DAYS="${BK_STALE_DAYS:-2}"
MODE="${1:-daily}"          # daily | push-only(커밋 직후)
mkdir -p "$LOG_DIR"; LOG="$LOG_DIR/runs.log"; OK="$LOG_DIR/last_success"
now(){ date '+%Y-%m-%dT%H:%M:%S%z'; }
notify(){ command -v osascript >/dev/null && osascript -e "display notification \"$1\" with title \"기술자산 백업\"" 2>/dev/null; echo "NOTIFY: $1" >&2; }
step(){ # step 이름 명령... → 실패 시 사유(마지막 오류 줄)를 기록
  local name=$1; shift; local out
  if out=$("$@" 2>&1); then STEPS+=("$name:ok"); else
    local why; why=$(printf '%s' "$out" | tail -n 2 | tr '\n"' ' ' | cut -c1-200)
    STEPS+=("$name:FAIL"); FAILS+=("$name: $why"); fi; }
STEPS=(); FAILS=(); START=$(date +%s)
# 오래 끊겼는지 먼저 확인 (지난 성공이 STALE_DAYS일 넘으면 알림)
if [ -f "$OK" ] && [ $(( (START - $(cat "$OK")) / 86400 )) -ge "$STALE_DAYS" ]; then
  notify "마지막 성공 백업이 ${STALE_DAYS}일 넘게 지났습니다"; fi
cd "$SRC" || { echo "{\"at\":\"$(now)\",\"mode\":\"$MODE\",\"result\":\"FAIL\",\"why\":\"SRC 없음: $SRC\"}" >> "$LOG"; notify "백업 실패: 원본 폴더 없음"; exit 1; }
for r in $(git remote); do step "push-$r" git push --quiet "$r" --all; step "tags-$r" git push --quiet "$r" --tags; done
if [ "$MODE" = daily ]; then
  step "fsck" git fsck --no-progress
  case "$NAS_FILES" in /Volumes/*) VOL="/Volumes/$(echo "$NAS_FILES" | cut -d/ -f3)"
    if ! mount | grep -q " on $VOL "; then STEPS+=("rsync-files:FAIL"); FAILS+=("rsync-files: NAS 볼륨($VOL)이 연결돼 있지 않음"); NAS_FILES=""; fi;; esac
  [ -n "$NAS_FILES" ] && step "rsync-files" rsync -a --exclude .git --exclude '.DS_Store' "$SRC/" "$NAS_FILES/"
fi
RESULT=ok; [ ${#FAILS[@]} -gt 0 ] && RESULT=FAIL
WHY=$(IFS='; '; echo "${FAILS[*]:-}")
printf '{"at":"%s","mode":"%s","result":"%s","sec":%d,"head":"%s","steps":"%s","why":"%s"}\n' \
  "$(now)" "$MODE" "$RESULT" $(( $(date +%s) - START )) "$(git rev-parse --short HEAD 2>/dev/null)" "${STEPS[*]}" "$WHY" >> "$LOG"
if [ $RESULT = ok ]; then [ "$MODE" = daily ] && date +%s > "$OK"; exit 0; fi
notify "백업 실패: $WHY"; exit 1
