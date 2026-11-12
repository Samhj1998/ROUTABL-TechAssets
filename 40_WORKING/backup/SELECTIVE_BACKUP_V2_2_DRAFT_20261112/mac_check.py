#!/usr/bin/env python3
"""Mac에서 한 번 실행: 자동 백업 최근 상태 + v2.2 plan(쓰기 없음) → MAC_CHECK_RESULT.json (경로 대신 이름·상태만)."""
import json, os, subprocess, sys, time
from pathlib import Path
HOME = Path.home(); HERE = Path(__file__).resolve().parent
LOG = HOME / "Library/Logs/ROUTABL-AssetBackup"
out = {"checked_at": time.strftime("%Y-%m-%d %H:%M:%S"), "log_dir_exists": LOG.is_dir(), "logs": []}
if LOG.is_dir():
    for p in sorted(LOG.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:15]:
        item = {"name": p.name, "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime)), "bytes": p.stat().st_size}
        if p.suffix == ".json" and p.stat().st_size < 200_000:
            try:
                j = json.loads(p.read_text(encoding="utf-8"))
                item["fields"] = {k: j[k] for k in ("status", "phase", "failure_type", "finished_at", "completed_at", "timestamp",
                                                     "snapshot_name", "manifest_name", "total_files", "returncode") if k in j}
            except Exception as e:
                item["read_error"] = type(e).__name__
        elif p.suffix in (".log", ".txt") and p.stat().st_size < 2_000_000:
            item["tail"] = p.read_text(encoding="utf-8", errors="replace").splitlines()[-5:]
        out["logs"].append(item)
r = subprocess.run([sys.executable, str(HERE / "ROUTABL_SelectiveSecureBackup_v2_2.py"), "plan"], capture_output=True, text=True, timeout=600)
out["v22_plan_returncode"] = r.returncode
try:
    j = json.loads(r.stdout)
    out["v22_plan"] = {k: j.get(k) for k in ("status", "source_manifest", "engine", "registry_assets_approved", "project_source_files",
                                           "managed_extra_files", "total_files", "total_source_bytes", "registry_drift_asset_ids",
                                           "registry_missing_asset_ids", "registry_rejected_asset_ids", "registry_same_path_superseded")}
except Exception:
    out["v22_plan_stderr"] = r.stderr[-400:]
for app in ("com.routabl.assetbackup.native.v042",):
    q = subprocess.run(["/bin/launchctl", "print", "gui/%d/%s" % (os.getuid(), app)], capture_output=True, text=True)
    out["agent_" + app] = {"loaded": q.returncode == 0,
                          "lines": [l.strip() for l in q.stdout.splitlines() if any(k in l for k in ("state =", "last exit", "runs ="))][:5]}
(HERE / "MAC_CHECK_RESULT.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("완료: Claude에게 '확인 끝'이라고 알려주세요.")
