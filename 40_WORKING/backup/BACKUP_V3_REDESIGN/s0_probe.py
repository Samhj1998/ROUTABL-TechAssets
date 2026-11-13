#!/usr/bin/env python3
"""S0 실패 원인 확인용 실행기 (2026-11-14). 기존 00_GUIDE 스크립트는 수정하지 않고 그대로 불러 실행만 한다.
기존 실행기가 버리는 '실패 이유'와 하위 단계의 마지막 오류 줄을 이 터미널 화면에만 보여준다(파일 기록 없음)."""
import importlib.util, subprocess, sys, traceback
from pathlib import Path
SRC = Path.home() / "ROUTABL-TechAssets/00_GUIDE/ROUTABL_MacToNasOneShot_v0_1.py"
spec = importlib.util.spec_from_file_location("oneshot", SRC)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
_orig = subprocess.run
def _run(args, *a, **k):
    r = _orig(args, *a, **k)
    name = Path(str(args[1])).name if len(args) > 1 else str(args)
    print(f"[하위 단계] {name} {' '.join(map(str, args[2:]))[:80]} → 종료코드 {r.returncode}", flush=True)
    if r.returncode != 0 and getattr(r, "stderr", None):
        print("  마지막 오류 줄:", *r.stderr.strip().splitlines()[-8:], sep="\n    ", flush=True)
    return r
m.subprocess.run = _run
sys.argv = [str(SRC), "run"]
try:
    rc = m.main(); print(f"\n결과: 종료코드 {rc} (0이면 성공)")
except SystemExit as e:
    print(f"\n결과: 종료 {e.code}")
except Exception as e:
    print(f"\n결과: 실패 — {type(e).__name__}: {e}"); traceback.print_exc(limit=3)
